"""
Common Crawl scanner for ArtLockr.

Searches Common Crawl index for publicly available creative works
(images, audio, etc.) that can be indexed in the public dataset catalogue.

Uses the CC Index API (https://index.commoncrawl.org/) which requires
no authentication and is free to query.
"""

import httpx
import asyncio
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Latest Common Crawl index – update periodically
CC_INDEX_API = "https://index.commoncrawl.org"
DEFAULT_CRAWL = "CC-MAIN-2024-10"   # update to latest available

# Content types we care about
SUPPORTED_CONTENT_TYPES = {
    "image/jpeg": ("image", "jpg"),
    "image/png": ("image", "png"),
    "image/gif": ("image", "gif"),
    "image/webp": ("image", "webp"),
    "audio/mpeg": ("audio", "mp3"),
    "audio/wav": ("audio", "wav"),
    "audio/ogg": ("audio", "ogg"),
    "audio/flac": ("audio", "flac"),
    "video/mp4": ("video", "mp4"),
    "video/webm": ("video", "webm"),
    "text/plain": ("text", "txt"),
}

# Public creative-work domains worth crawling
CREATIVE_DOMAINS = [
    "commons.wikimedia.org",
    "freesound.org",
    "pixabay.com",
    "unsplash.com",
    "pexels.com",
    "openverse.org",
    "flickr.com",
    "archive.org",
    "soundcloud.com",
    "ccmixter.org",
]


async def search_cc_index(
    url_pattern: str,
    crawl_id: str = DEFAULT_CRAWL,
    limit: int = 100,
) -> list[dict]:
    """
    Query the Common Crawl CDX Index Server for URLs matching a pattern.
    Returns a list of records with url, mime, status, etc.

    Example url_pattern: "*.freesound.org/sounds/*"
    """
    params = {
        "url": url_pattern,
        "output": "json",
        "limit": limit,
        "fl": "url,mime,status,filename,offset,length,timestamp",
        "filter": "status:200",
    }

    api_url = f"{CC_INDEX_API}/{crawl_id}-index"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(api_url, params=params)
            resp.raise_for_status()

            results = []
            for line in resp.text.strip().splitlines():
                if line:
                    import json
                    try:
                        results.append(json.loads(line))
                    except Exception:
                        pass
            return results

    except httpx.HTTPError as e:
        logger.warning(f"CC index query failed for {url_pattern}: {e}")
        return []


async def scan_creative_domain(
    domain: str,
    crawl_id: str = DEFAULT_CRAWL,
    limit: int = 50,
) -> list[dict]:
    """
    Scan a single creative domain for supported media files.
    Returns normalised PublicDatasetEntry-compatible dicts.
    """
    entries = []

    for mime_type, (work_type, fmt) in SUPPORTED_CONTENT_TYPES.items():
        pattern = f"*.{domain}/*"
        results = await search_cc_index(pattern, crawl_id=crawl_id, limit=limit)

        for r in results:
            if r.get("mime", "").split(";")[0].strip() != mime_type:
                continue

            entries.append({
                "url": r.get("url"),
                "content_type": mime_type,
                "work_type": work_type,
                "file_format": fmt,
                "dataset_source": "common_crawl",
                "crawl_id": crawl_id,
                "discovered_at": datetime.utcnow(),
                "indexed": False,
            })

    return entries


async def scan_multiple_domains(
    domains: Optional[list[str]] = None,
    crawl_id: str = DEFAULT_CRAWL,
    limit_per_domain: int = 20,
) -> list[dict]:
    """
    Scan multiple creative domains concurrently.
    """
    targets = domains or CREATIVE_DOMAINS
    tasks = [
        scan_creative_domain(domain, crawl_id=crawl_id, limit=limit_per_domain)
        for domain in targets
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_entries = []
    for domain, result in zip(targets, results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to scan {domain}: {result}")
        else:
            all_entries.extend(result)

    logger.info(f"Common Crawl scan complete: {len(all_entries)} entries found")
    return all_entries


def get_available_crawls() -> list[str]:
    """
    Return a hardcoded list of recent Common Crawl identifiers.
    In production, fetch from https://index.commoncrawl.org/collinfo.json
    """
    return [
        "CC-MAIN-2024-10",
        "CC-MAIN-2023-50",
        "CC-MAIN-2023-40",
        "CC-MAIN-2023-23",
        "CC-MAIN-2023-14",
    ]


# ─────────────────────────────────────────
# Other public creative datasets (non-CC)
# ─────────────────────────────────────────

async def search_wikimedia_commons(query: str, limit: int = 20) -> list[dict]:
    """
    Search Wikimedia Commons for freely licensed images using the API.
    All returned content is CC-licensed or public domain.
    """
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,   # File namespace
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        entries = []
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            mime = info.get("mime", "")
            work_type, fmt = SUPPORTED_CONTENT_TYPES.get(mime, (None, None))
            if not work_type:
                continue

            extmeta = info.get("extmetadata", {})
            license_val = extmeta.get("LicenseShortName", {}).get("value", "")

            entries.append({
                "url": info.get("url"),
                "content_type": mime,
                "work_type": work_type,
                "file_format": fmt,
                "file_size": info.get("size"),
                "dataset_source": "wikimedia",
                "crawl_id": None,
                "license_detected": license_val,
                "title_detected": page.get("title", "").replace("File:", ""),
                "discovered_at": datetime.utcnow(),
                "indexed": False,
            })

        return entries

    except Exception as e:
        logger.warning(f"Wikimedia search failed: {e}")
        return []


async def search_freesound(query: str, api_key: str, limit: int = 20) -> list[dict]:
    """
    Search Freesound.org for CC-licensed audio files.
    Requires a Freesound API key (free registration).
    """
    url = "https://freesound.org/apiv2/search/text/"
    params = {
        "query": query,
        "token": api_key,
        "page_size": limit,
        "fields": "id,name,url,filesize,duration,license,type",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        entries = []
        for sound in data.get("results", []):
            entries.append({
                "url": sound.get("url"),
                "content_type": f"audio/{sound.get('type', 'mp3')}",
                "work_type": "audio",
                "file_format": sound.get("type", "mp3"),
                "file_size": sound.get("filesize"),
                "dataset_source": "freesound",
                "crawl_id": None,
                "license_detected": sound.get("license"),
                "title_detected": sound.get("name"),
                "discovered_at": datetime.utcnow(),
                "indexed": False,
            })

        return entries

    except Exception as e:
        logger.warning(f"Freesound search failed: {e}")
        return []
