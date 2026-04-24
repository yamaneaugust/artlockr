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

import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ArtLock Sync Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
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


# ── Perceptual hashing (inline, no imagehash dep) ───────────────────────

_DCT_CACHE: dict[int, np.ndarray] = {}

def _dct_matrix(n: int) -> np.ndarray:
    if n not in _DCT_CACHE:
        k = np.arange(n)
        D = np.cos(np.pi * k[:, None] * (2 * k[None, :] + 1) / (2 * n))
        D[0] /= np.sqrt(n)
        D[1:] *= np.sqrt(2.0 / n)
        _DCT_CACHE[n] = D
    return _DCT_CACHE[n]

def _phash(img: Image.Image, hash_size: int = 8) -> str:
    """Perceptual hash via 2D DCT."""
    size = hash_size * 4
    gray = img.convert("L").resize((size, size), Image.LANCZOS)
    pixels = np.array(gray, dtype=float)
    D = _dct_matrix(size)
    dct = D @ pixels @ D.T
    low = dct[:hash_size, :hash_size]
    med = low[0:, 1:].mean()  # exclude DC component
    return "".join("1" if v > med else "0" for v in low.flatten())

def _dhash(img: Image.Image, hash_size: int = 8) -> str:
    """Difference hash (horizontal gradient)."""
    gray = img.convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels = np.array(gray)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return "".join("1" if v else "0" for v in diff.flatten())

def _ahash(img: Image.Image, hash_size: int = 8) -> str:
    """Average hash."""
    gray = img.convert("L").resize((hash_size, hash_size), Image.LANCZOS)
    pixels = np.array(gray, dtype=float)
    avg = pixels.mean()
    return "".join("1" if v > avg else "0" for v in pixels.flatten())

def compute_image_hashes(img: Image.Image) -> dict:
    return {
        "phash": _phash(img),
        "dhash": _dhash(img),
        "ahash": _ahash(img),
    }

def hamming_distance(h1: str, h2: str) -> int:
    if len(h1) != len(h2):
        return 999
    return sum(a != b for a, b in zip(h1, h2))

def calculate_similarity(hashes1: dict, hashes2: dict) -> float:
    if not hashes1 or not hashes2:
        return 0.0
    max_dist = 64
    weights = {"phash": 0.5, "dhash": 0.25, "ahash": 0.25}
    total_w = 0.0
    weighted_sum = 0.0
    for ht, w in weights.items():
        if ht in hashes1 and ht in hashes2:
            dist = hamming_distance(hashes1[ht], hashes2[ht])
            weighted_sum += max(0.0, 1 - dist / max_dist) * w
            total_w += w
    return weighted_sum / total_w if total_w else 0.0


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
    perceptual_hashes: dict | None = None


def _hashes_from_data_url(data_url: str) -> dict | None:
    if not data_url:
        return None
    try:
        raw = base64.b64decode(data_url.split(",")[1] if "," in data_url else data_url)
        img = Image.open(io.BytesIO(raw))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((512, 512))
        return compute_image_hashes(img)
    except Exception:
        return None


@app.get("/sync/works")
def list_works():
    return {"items": [{k: v for k, v in w.items() if k != "perceptual_hashes"} for w in store["works"]]}


@app.post("/sync/works")
def create_work(work: WorkCreate):
    data = work.model_dump()
    if not data.get("created_at"):
        data["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if not data.get("perceptual_hashes") and data.get("preview_url"):
        data["perceptual_hashes"] = _hashes_from_data_url(data["preview_url"])
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


# ── Copyright Detection ──────────────────────────────────────────────────

class CopyrightDetectRequest(BaseModel):
    image_data: str
    filename: str
    file_size: int | None = None
    file_type: str | None = None


@app.post("/api/v1/copyright/detect")
def detect_copyright(req: CopyrightDetectRequest):
    try:
        raw = base64.b64decode(req.image_data.split(",")[1] if "," in req.image_data else req.image_data)
        img = Image.open(io.BytesIO(raw))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((512, 512))
        uploaded_hashes = compute_image_hashes(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {e}")

    matches = []
    store_updated = False

    for work in store["works"]:
        stored_hashes = work.get("perceptual_hashes")
        if not stored_hashes and work.get("preview_url"):
            stored_hashes = _hashes_from_data_url(work["preview_url"])
            if stored_hashes:
                work["perceptual_hashes"] = stored_hashes
                store_updated = True
        if not stored_hashes:
            continue

        similarity = calculate_similarity(uploaded_hashes, stored_hashes)
        if similarity >= 0.60:
            listing = next((l for l in store["listings"] if l.get("work_id") == work["id"]), None)
            name = work.get("title", "Registered Artwork")
            if work.get("owner_username"):
                name = f"{name} by {work['owner_username']}"
            matches.append({
                "source": name,
                "url": f"/marketplace/{listing['id']}" if listing else "#",
                "similarity": round(similarity, 3),
                "work_id": work["id"],
                "registered_date": work.get("created_at", ""),
            })

    if store_updated:
        save_store(store)

    matches.sort(key=lambda m: m["similarity"], reverse=True)

    if matches:
        top = matches[0]["similarity"]
        if top >= 0.95:
            status, message = "match_found", f"Exact or near-exact match found ({int(top * 100)}% similarity). This image is registered in our database."
        elif top >= 0.85:
            status, message = "match_found", f"High confidence match found ({int(top * 100)}% similarity). This image closely matches registered artwork."
        elif top >= 0.70:
            status, message = "uncertain", f"Potential match detected ({int(top * 100)}% similarity). The images are similar but may have modifications."
        else:
            status, message = "uncertain", f"Low confidence match ({int(top * 100)}% similarity). Minor similarities detected."
        confidence = top
    else:
        status = "clean"
        confidence = 0.95
        message = "No matches found in our registered works database. This image does not appear to match any protected artwork."

    return {
        "status": status,
        "confidence": confidence,
        "matches": matches[:10],
        "message": message,
        "scanned_works": len(store["works"]),
        "hash_algorithms": ["pHash", "dHash", "aHash"],
    }
