"""
Marketplace API endpoints.

Covers:
- Browsing & searching listings
- Uploading creative works and creating listings (artists)
- Purchasing a license (companies)
- Viewing purchases / license keys
- Marketplace stats
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
import hashlib, os, shutil
from datetime import datetime

from backend.app.models.database import (
    User, CreativeWork, Listing, Purchase,
    PublicDatasetEntry,
)
from backend.app.services import marketplace_service, common_crawl
from backend.app.core.database import get_db

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
FEATURES_DIR = os.getenv("FEATURES_DIR", "data/features")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FEATURES_DIR, exist_ok=True)


# ─────────────────────────────────────────
# Browse & Search
# ─────────────────────────────────────────

@router.get("/listings")
def browse_listings(
    work_type: Optional[str] = Query(None),
    license_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = marketplace_service.browse_listings(
        db,
        work_type=work_type,
        license_type=license_type,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )

    items = []
    for listing in result["items"]:
        work = listing.work
        artist = listing.artist
        items.append({
            "id": listing.id,
            "title": listing.title,
            "description": listing.description,
            "price": float(listing.price),
            "license_type": listing.license_type,
            "status": listing.status,
            "featured": listing.featured,
            "work": {
                "id": work.id,
                "work_type": work.work_type,
                "file_format": work.file_format,
                "tags": work.tags,
                "preview_url": work.preview_url,
                "source": work.source,
            },
            "artist": {
                "id": artist.id,
                "username": artist.username,
                "display_name": artist.artist_profile.display_name if artist.artist_profile else artist.username,
                "avatar_url": artist.avatar_url,
                "verified": artist.artist_profile.verified_artist if artist.artist_profile else False,
            },
            "created_at": listing.created_at.isoformat(),
        })

    return {**result, "items": items}


@router.get("/listings/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = marketplace_service.get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    work = listing.work
    artist = listing.artist
    sales_count = len([p for p in listing.purchases if p.status == "completed"])

    return {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "price": float(listing.price),
        "license_type": listing.license_type,
        "license_details": listing.license_details,
        "max_buyers": listing.max_buyers,
        "sales_count": sales_count,
        "status": listing.status,
        "work": {
            "id": work.id,
            "work_type": work.work_type,
            "file_format": work.file_format,
            "file_size": work.file_size,
            "duration": work.duration,
            "dimensions": work.dimensions,
            "tags": work.tags,
            "style": work.style,
            "preview_url": work.preview_url,
            "source": work.source,
            "source_dataset": work.source_dataset,
        },
        "artist": {
            "id": artist.id,
            "username": artist.username,
            "display_name": artist.artist_profile.display_name if artist.artist_profile else artist.username,
            "bio": artist.bio,
            "avatar_url": artist.avatar_url,
            "website": artist.website,
            "verified": artist.artist_profile.verified_artist if artist.artist_profile else False,
            "total_sales": artist.artist_profile.total_sales if artist.artist_profile else 0,
        },
        "created_at": listing.created_at.isoformat(),
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return marketplace_service.marketplace_stats(db)


# ─────────────────────────────────────────
# Upload Work & Create Listing (Artists)
# ─────────────────────────────────────────

@router.post("/works/upload")
async def upload_work(
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),           # comma-separated
    style: str = Form("general"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # In real app: current_user = Depends(get_current_user)
    artist_id: int = Form(...),     # TODO: replace with JWT auth
):
    # Validate file type
    content_type = file.content_type or ""
    work_type, fmt = _detect_work_type(content_type, file.filename or "")
    if not work_type:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    # Read and hash
    data = await file.read()
    file_hash = hashlib.sha256(data).hexdigest()

    if db.query(CreativeWork).filter(CreativeWork.file_hash == file_hash).first():
        raise HTTPException(status_code=409, detail="This file has already been uploaded")

    # Save file temporarily for feature extraction; can delete after
    filename = f"{file_hash}.{fmt}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(data)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    work = CreativeWork(
        owner_id=artist_id,
        title=title,
        description=description,
        work_type=work_type,
        file_format=fmt,
        file_size=len(data),
        file_hash=file_hash,
        tags=tag_list,
        style=style,
        source="upload",
        image_deleted=False,
        upload_proof_hash=hashlib.sha256(
            f"{file_hash}{artist_id}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest(),
        created_at=datetime.utcnow(),
    )
    db.add(work)
    db.commit()
    db.refresh(work)

    return {"work_id": work.id, "file_hash": file_hash, "work_type": work_type}


@router.post("/listings/create")
def create_listing(
    work_id: int = Form(...),
    artist_id: int = Form(...),    # TODO: replace with JWT auth
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    license_type: str = Form(...),
    license_details: str = Form(""),
    max_buyers: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    work = db.query(CreativeWork).filter(
        CreativeWork.id == work_id,
        CreativeWork.owner_id == artist_id,
    ).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found or not owned by you")

    if work.listing:
        raise HTTPException(status_code=409, detail="This work already has an active listing")

    listing = marketplace_service.create_listing(
        db,
        artist_id=artist_id,
        work_id=work_id,
        title=title,
        description=description,
        price=Decimal(str(price)),
        license_type=license_type,
        license_details=license_details or None,
        max_buyers=max_buyers,
    )
    return {"listing_id": listing.id, "status": listing.status}


# ─────────────────────────────────────────
# Purchase Flow (Companies)
# ─────────────────────────────────────────

@router.post("/listings/{listing_id}/purchase")
def purchase_listing(
    listing_id: int,
    buyer_id: int,           # TODO: replace with JWT auth
    db: Session = Depends(get_db),
):
    try:
        result = marketplace_service.initiate_purchase(db, listing_id, buyer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/purchases")
def my_purchases(
    buyer_id: int,           # TODO: replace with JWT auth
    db: Session = Depends(get_db),
):
    purchases = marketplace_service.get_buyer_purchases(db, buyer_id)
    return [
        {
            "id": p.id,
            "listing_id": p.listing_id,
            "listing_title": p.listing.title,
            "amount": float(p.amount),
            "license_key": p.license_key,
            "license_type": p.listing.license_type,
            "status": p.status,
            "purchased_at": p.purchased_at.isoformat(),
            "download_expires_at": p.download_expires_at.isoformat() if p.download_expires_at else None,
        }
        for p in purchases
    ]


@router.get("/license/{license_key}")
def verify_license(license_key: str, db: Session = Depends(get_db)):
    purchase = marketplace_service.get_purchase_by_license(db, license_key)
    if not purchase:
        raise HTTPException(status_code=404, detail="License not found")
    return {
        "valid": purchase.status == "completed",
        "listing_title": purchase.listing.title,
        "license_type": purchase.listing.license_type,
        "buyer_id": purchase.buyer_id,
        "purchased_at": purchase.purchased_at.isoformat(),
    }


# ─────────────────────────────────────────
# Public Dataset Discovery
# ─────────────────────────────────────────

@router.get("/public-datasets")
def list_public_datasets(
    work_type: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(PublicDatasetEntry)
    if work_type:
        query = query.filter(PublicDatasetEntry.work_type == work_type)
    if source:
        query = query.filter(PublicDatasetEntry.dataset_source == source)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "items": [
            {
                "id": e.id,
                "url": e.url,
                "work_type": e.work_type,
                "file_format": e.file_format,
                "dataset_source": e.dataset_source,
                "license_detected": e.license_detected,
                "title_detected": e.title_detected,
                "author_detected": e.author_detected,
                "discovered_at": e.discovered_at.isoformat(),
            }
            for e in items
        ],
    }


@router.post("/public-datasets/scan")
async def trigger_crawl_scan(
    domains: Optional[list[str]] = None,
    db: Session = Depends(get_db),
):
    """Trigger an async Common Crawl scan (admin use)."""
    entries = await common_crawl.scan_multiple_domains(
        domains=domains, limit_per_domain=10
    )

    saved = 0
    for entry in entries:
        if entry.get("url") and not db.query(PublicDatasetEntry).filter(
            PublicDatasetEntry.url == entry["url"]
        ).first():
            db.add(PublicDatasetEntry(**entry))
            saved += 1

    db.commit()
    return {"scanned": len(entries), "saved": saved}


@router.get("/public-datasets/search/wikimedia")
async def search_wikimedia(q: str = Query(...), limit: int = Query(20, le=50)):
    results = await common_crawl.search_wikimedia_commons(q, limit=limit)
    return {"results": results, "count": len(results)}


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _detect_work_type(content_type: str, filename: str) -> tuple:
    mapping = {
        "image/jpeg": ("image", "jpg"),
        "image/png": ("image", "png"),
        "image/gif": ("image", "gif"),
        "image/webp": ("image", "webp"),
        "audio/mpeg": ("audio", "mp3"),
        "audio/mp3": ("audio", "mp3"),
        "audio/wav": ("audio", "wav"),
        "audio/ogg": ("audio", "ogg"),
        "audio/flac": ("audio", "flac"),
        "video/mp4": ("video", "mp4"),
        "video/webm": ("video", "webm"),
        "text/plain": ("text", "txt"),
        "application/zip": ("dataset", "zip"),
    }
    if content_type in mapping:
        return mapping[content_type]

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_map = {
        "jpg": ("image", "jpg"), "jpeg": ("image", "jpg"),
        "png": ("image", "png"), "gif": ("image", "gif"),
        "webp": ("image", "webp"),
        "mp3": ("audio", "mp3"), "wav": ("audio", "wav"),
        "ogg": ("audio", "ogg"), "flac": ("audio", "flac"),
        "mp4": ("video", "mp4"), "webm": ("video", "webm"),
        "txt": ("text", "txt"), "zip": ("dataset", "zip"),
    }
    return ext_map.get(ext, (None, None))
