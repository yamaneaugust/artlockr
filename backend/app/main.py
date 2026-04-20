"""
ArtLock – Creative Data Marketplace

A platform where artists sell licensed creative works to AI companies.
Artists connect via Stripe Connect; companies pay via Stripe Checkout.
Public dataset discovery via Common Crawl + Wikimedia.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.marketplace_endpoints import router as marketplace_router
from app.api.stripe_endpoints import router as stripe_router
from app.api.profile_endpoints import router as profile_router

app = FastAPI(
    title="ArtLock – Creative Data Marketplace",
    version="2.0.0",
    description="""
    ArtLock connects artists with AI companies so that creative works can be
    legally licensed as training data.

    **Artists** upload images, audio, video, and text; set license terms and prices;
    get paid automatically via Stripe Connect.

    **AI Companies** browse the marketplace, purchase licenses, and download
    verified creative datasets.

    **Public dataset discovery** indexes freely-licensed works from Common Crawl,
    Wikimedia Commons, Freesound, and more.

    ## Key features
    - Multi-format uploads (image / audio / video / text / dataset)
    - License types: CC0, CC-BY, non-exclusive, exclusive, custom
    - Stripe Connect for artist payouts (10% platform fee)
    - Stripe Checkout for company purchases
    - Common Crawl / Wikimedia public-domain catalogue
    - License key verification
    """,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(profile_router)
app.include_router(marketplace_router)
app.include_router(stripe_router)

# Also mount under /api/v1 so built frontends with old URL still work
from fastapi import APIRouter as _APIRouter
_v1 = _APIRouter(prefix="/api/v1")
_v1.include_router(profile_router)
_v1.include_router(marketplace_router)
_v1.include_router(stripe_router)
app.include_router(_v1)


# ── Health / root ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Meta"])
async def root():
    return {
        "name": "ArtLock Creative Marketplace",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "register": "/profiles/register",
            "login": "/profiles/login",
            "browse": "/marketplace/listings",
            "upload": "/marketplace/works/upload",
            "stats": "/marketplace/stats",
            "public_datasets": "/marketplace/public-datasets",
            "stripe_onboard": "/stripe/connect/onboard",
            "stripe_webhook": "/stripe/webhook",
        },
    }


@app.get("/health", tags=["Meta"])
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
