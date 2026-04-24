"""
ArtLock Simple Backend - Minimal sync server for marketplace/works/purchases

Stores data in a JSON file for persistence. Deploys easily to Railway
with zero configuration. No database required.
"""
import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ArtLock Sync Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store data in /data if available (Railway volume), otherwise /tmp
DATA_DIR = Path(os.getenv("DATA_DIR", "/tmp"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORE_FILE = DATA_DIR / "artlock_data.json"

def load_store() -> dict[str, list]:
    if STORE_FILE.exists():
        try:
            return json.loads(STORE_FILE.read_text())
        except Exception:
            pass
    return {"works": [], "listings": [], "purchases": [], "requests": []}

def save_store(data: dict[str, list]) -> None:
    STORE_FILE.write_text(json.dumps(data, indent=2))

# Load on startup
store = load_store()


@app.get("/")
def root():
    return {
        "name": "ArtLock Sync Backend",
        "status": "ok",
        "counts": {k: len(v) for k, v in store.items()},
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# ── Works ───────────────────────────────────────────────────────────────

class WorkCreate(BaseModel):
    id: int
    owner_id: int
    owner_username: str | None = None
    title: str
    description: str | None = ""
    tags: list[str] = []
    work_type: str = "image"
    file_format: str | None = None
    file_size: int | None = None
    file_hash: str | None = None
    fingerprint: str | None = None
    preview_url: str | None = None
    created_at: str | None = None


@app.get("/sync/works")
def list_works():
    return {"items": store["works"]}


@app.post("/sync/works")
def create_work(work: WorkCreate):
    data = work.model_dump()
    if not data.get("created_at"):
        data["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    # Dedupe by id
    store["works"] = [w for w in store["works"] if w.get("id") != data["id"]]
    store["works"].append(data)
    save_store(store)
    return {"ok": True, "work_id": data["id"]}


# ── Listings ────────────────────────────────────────────────────────────

class ListingCreate(BaseModel):
    id: int
    work_id: int
    title: str
    description: str | None = ""
    price: float
    license_type: str = "non_exclusive"
    license_details: str | None = ""
    max_buyers: int | None = None
    work: dict[str, Any] = {}
    artist: dict[str, Any] = {}
    created_at: str | None = None
    sales_count: int | None = 0
    is_draft: bool = False


@app.get("/sync/listings")
def list_listings():
    return {"items": store["listings"], "total": len(store["listings"])}


@app.get("/sync/listings/{listing_id}")
def get_listing(listing_id: int):
    for l in store["listings"]:
        if l.get("id") == listing_id:
            return l
    raise HTTPException(status_code=404, detail="Listing not found")


@app.post("/sync/listings")
def create_listing(listing: ListingCreate):
    data = listing.model_dump()
    if not data.get("created_at"):
        data["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    # Replace any existing listing with the same id
    store["listings"] = [l for l in store["listings"] if l.get("id") != data["id"]]
    store["listings"].append(data)
    save_store(store)
    return {"ok": True, "listing_id": data["id"]}


@app.delete("/sync/listings/{listing_id}")
def delete_listing(listing_id: int):
    store["listings"] = [l for l in store["listings"] if l.get("id") != listing_id]
    save_store(store)
    return {"ok": True}


# ── Purchases ───────────────────────────────────────────────────────────

class PurchaseCreate(BaseModel):
    id: int
    listing_id: int
    buyer_id: int
    buyer_username: str | None = None
    license_key: str
    price_paid: float
    license_type: str | None = None
    listing_title: str | None = None
    work_preview_url: str | None = None
    artist_username: str | None = None
    purchased_at: str | None = None


@app.get("/sync/purchases")
def list_purchases(buyer_id: int | None = None):
    items = store["purchases"]
    if buyer_id is not None:
        items = [p for p in items if p.get("buyer_id") == buyer_id]
    return {"items": items}


@app.post("/sync/purchases")
def create_purchase(purchase: PurchaseCreate):
    data = purchase.model_dump()
    if not data.get("purchased_at"):
        data["purchased_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    store["purchases"].append(data)
    # Increment sales_count on the listing
    for l in store["listings"]:
        if l.get("id") == data["listing_id"]:
            l["sales_count"] = (l.get("sales_count") or 0) + 1
            break
    save_store(store)
    return {"ok": True, "purchase_id": data["id"]}


# ── Requests ────────────────────────────────────────────────────────────

class RequestCreate(BaseModel):
    id: int
    company_id: int
    company_username: str | None = None
    company_name: str | None = None
    title: str
    description: str | None = ""
    work_type: str = "image"
    license_type: str = "any"
    quantity: int | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    deadline: str | None = None
    requirements: str | None = ""
    status: str = "open"
    created_at: str | None = None


@app.get("/sync/requests")
def list_requests():
    return {"items": store["requests"]}


@app.post("/sync/requests")
def create_request(req: RequestCreate):
    data = req.model_dump()
    if not data.get("created_at"):
        data["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    store["requests"].append(data)
    save_store(store)
    return {"ok": True, "request_id": data["id"]}


# ── Stats ───────────────────────────────────────────────────────────────

@app.get("/sync/stats")
def stats():
    return {
        "total_listings": len(store["listings"]),
        "total_works": len(store["works"]),
        "total_purchases": len(store["purchases"]),
        "total_requests": len(store["requests"]),
        "total_artists": len(set(w.get("owner_id") for w in store["works"] if w.get("owner_id"))),
        "total_companies": len(set(p.get("buyer_id") for p in store["purchases"] if p.get("buyer_id"))),
        "total_volume_usd": sum(p.get("price_paid", 0) for p in store["purchases"]),
    }


# ── Copyright Detection (Mock/Demo) ────────────────────────────────────

class CopyrightDetectRequest(BaseModel):
    file_hash: str
    filename: str
    file_size: int | None = None
    file_type: str | None = None


@app.post("/api/v1/copyright/detect")
def detect_copyright(req: CopyrightDetectRequest):
    """
    Mock copyright detection - simulates web crawling with realistic results.
    Uses file hash to deterministically generate demo matches.
    """
    # Use hash to seed deterministic results (same file = same results)
    hash_int = int(req.file_hash[:8], 16) if req.file_hash else 0

    # Simulate processing delay (realistic for web crawl)
    time.sleep(0.5)

    # Demo match sources (realistic-looking websites)
    mock_sources = [
        {"name": "DeviantArt", "domain": "deviantart.com"},
        {"name": "ArtStation", "domain": "artstation.com"},
        {"name": "Pinterest", "domain": "pinterest.com"},
        {"name": "Behance", "domain": "behance.net"},
        {"name": "Instagram", "domain": "instagram.com"},
        {"name": "Flickr", "domain": "flickr.com"},
        {"name": "Tumblr", "domain": "tumblr.com"},
        {"name": "Reddit", "domain": "reddit.com"},
        {"name": "Wikimedia Commons", "domain": "commons.wikimedia.org"},
        {"name": "Unsplash", "domain": "unsplash.com"},
    ]

    # Generate 0-3 matches based on hash
    num_matches = (hash_int % 4)  # 0, 1, 2, or 3 matches
    matches = []

    for i in range(num_matches):
        source_idx = (hash_int + i * 17) % len(mock_sources)
        source = mock_sources[source_idx]

        # Generate similarity score (60-99%)
        similarity = 0.6 + ((hash_int + i * 23) % 40) / 100.0

        # Create realistic-looking URL
        image_id = abs(hash_int + i * 1000) % 999999
        url = f"https://{source['domain']}/art/{image_id}"

        matches.append({
            "source": f"{source['name']} - User artwork",
            "url": url,
            "similarity": round(similarity, 2),
        })

    # Sort by similarity (highest first)
    matches.sort(key=lambda m: m["similarity"], reverse=True)

    # Determine status and confidence
    if matches:
        max_similarity = matches[0]["similarity"]
        if max_similarity >= 0.9:
            status = "match_found"
            message = f"High confidence match found on the web ({int(max_similarity * 100)}% similarity). This image appears on {len(matches)} website(s)."
        else:
            status = "uncertain"
            message = f"Potential match detected with {int(max_similarity * 100)}% similarity. Review the {len(matches)} source(s) below."
        confidence = max_similarity
    else:
        status = "clean"
        confidence = 0.95
        message = "No similar images found on the web. This appears to be original or not widely distributed."

    return {
        "status": status,
        "confidence": confidence,
        "matches": matches,
        "message": message,
        "scanned_sources": ["Google Images", "TinEye", "Bing Visual Search", "Yandex Images"] if matches else [],
    }
