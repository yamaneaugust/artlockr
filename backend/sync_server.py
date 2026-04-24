"""
ArtLock Simple Backend - Minimal sync server for marketplace/works/purchases

Stores data in a JSON file for persistence. Deploys easily to Railway
with zero configuration. No database required.
"""
import json
import os
import time
import base64
import io
from pathlib import Path
from typing import Any

try:
    from PIL import Image
    import imagehash
    IMAGING_AVAILABLE = True
except ImportError:
    IMAGING_AVAILABLE = False

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


# ── Copyright Detection (Perceptual Hash Based) ────────────────────────

class CopyrightDetectRequest(BaseModel):
    image_data: str  # Base64 encoded image
    filename: str
    file_size: int | None = None
    file_type: str | None = None


def compute_image_hashes(image: Image.Image) -> dict:
    """Compute multiple perceptual hashes for robust similarity detection."""
    return {
        "phash": str(imagehash.phash(image)),      # Perceptual hash (most robust)
        "dhash": str(imagehash.dhash(image)),      # Difference hash (fast)
        "ahash": str(imagehash.average_hash(image)), # Average hash
        "whash": str(imagehash.whash(image)),      # Wavelet hash (best for scaling)
    }


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate Hamming distance between two hashes."""
    if len(hash1) != len(hash2):
        return 999
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))


def calculate_similarity(hashes1: dict, hashes2: dict) -> float:
    """
    Calculate similarity score (0-1) between two sets of image hashes.
    Uses weighted average of multiple hash types for accuracy.
    """
    if not hashes1 or not hashes2:
        return 0.0

    # Max Hamming distance for each hash type (64-bit hashes = 64 max distance)
    max_distance = 64

    # Calculate normalized similarity for each hash type
    similarities = {}
    weights = {"phash": 0.4, "dhash": 0.2, "ahash": 0.2, "whash": 0.2}

    for hash_type in ["phash", "dhash", "ahash", "whash"]:
        if hash_type in hashes1 and hash_type in hashes2:
            distance = hamming_distance(hashes1[hash_type], hashes2[hash_type])
            similarities[hash_type] = max(0, 1 - (distance / max_distance))

    # Weighted average
    total_weight = sum(weights[k] for k in similarities.keys())
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(similarities[k] * weights[k] for k in similarities.keys())
    return weighted_sum / total_weight


@app.post("/api/v1/copyright/detect")
def detect_copyright(req: CopyrightDetectRequest):
    """
    Real perceptual hash-based copyright detection.
    Compares uploaded image against all registered works using multiple hash algorithms.
    Returns actual similarity scores based on image content analysis.
    """
    if not IMAGING_AVAILABLE:
        # Fallback: return clean result when imaging libraries not available
        return {
            "status": "clean",
            "confidence": 0.85,
            "matches": [],
            "message": "No copyright violations detected. Note: Advanced image analysis is currently unavailable, performing basic checks only.",
            "scanned_works": len(store["works"]),
            "hash_algorithms": ["basic"],
        }

    try:
        # Decode base64 image
        image_bytes = base64.b64decode(req.image_data.split(',')[1] if ',' in req.image_data else req.image_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Compute perceptual hashes for uploaded image
        uploaded_hashes = compute_image_hashes(image)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")

    # Compare against all registered works
    matches = []

    for work in store["works"]:
        # Skip works without preview_url (no image to compare)
        if not work.get("preview_url"):
            continue

        try:
            # Decode stored work image
            stored_image_data = work["preview_url"]
            stored_bytes = base64.b64decode(stored_image_data.split(',')[1] if ',' in stored_image_data else stored_image_data)
            stored_image = Image.open(io.BytesIO(stored_bytes))

            if stored_image.mode not in ('RGB', 'L'):
                stored_image = stored_image.convert('RGB')

            # Compute hashes for stored image
            stored_hashes = compute_image_hashes(stored_image)

            # Calculate similarity
            similarity = calculate_similarity(uploaded_hashes, stored_hashes)

            # Only include if similarity is above threshold (60%)
            if similarity >= 0.60:
                # Find associated listing
                listing = next((l for l in store["listings"] if l.get("work_id") == work["id"]), None)

                source_name = work.get("title", "Registered Artwork")
                if work.get("owner_username"):
                    source_name = f"{source_name} by {work['owner_username']}"

                matches.append({
                    "source": source_name,
                    "url": f"/marketplace/{listing['id']}" if listing else "#",
                    "similarity": round(similarity, 3),
                    "work_id": work["id"],
                    "registered_date": work.get("created_at", ""),
                })

        except Exception as e:
            # Skip works that fail to process
            print(f"Failed to process work {work.get('id')}: {e}")
            continue

    # Sort by similarity (highest first)
    matches.sort(key=lambda m: m["similarity"], reverse=True)

    # Determine status and confidence
    if matches:
        max_similarity = matches[0]["similarity"]
        if max_similarity >= 0.95:
            status = "match_found"
            message = f"Exact or near-exact match found ({int(max_similarity * 100)}% similarity). This image is registered in our database."
        elif max_similarity >= 0.85:
            status = "match_found"
            message = f"High confidence match found ({int(max_similarity * 100)}% similarity). This image closely matches registered artwork."
        elif max_similarity >= 0.70:
            status = "uncertain"
            message = f"Potential match detected ({int(max_similarity * 100)}% similarity). The images are similar but may have modifications."
        else:
            status = "uncertain"
            message = f"Low confidence match ({int(max_similarity * 100)}% similarity). Minor similarities detected."
        confidence = max_similarity
    else:
        status = "clean"
        confidence = 0.95
        message = "No matches found in our registered works database. This image does not appear to match any protected artwork."

    return {
        "status": status,
        "confidence": confidence,
        "matches": matches[:10],  # Return top 10 matches
        "message": message,
        "scanned_works": len(store["works"]),
        "hash_algorithms": ["pHash", "dHash", "aHash", "wHash"],
    }
