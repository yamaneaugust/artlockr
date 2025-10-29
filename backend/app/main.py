from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.endpoints import router as api_router

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ArtLockr - AI-Powered Copyright Detection API

    This API helps artists protect their intellectual property by detecting
    AI-generated artwork that may have been trained on or copied from their
    original works.

    Features:
    - Upload original artwork
    - Detect copyright infringement using ResNet-based similarity matching
    - API gating to block organizations from accessing protected artwork
    - Comprehensive tracking and reporting
    """
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "endpoints": {
            "upload_artwork": f"{settings.API_V1_STR}/upload-artwork",
            "detect_copyright": f"{settings.API_V1_STR}/detect-copyright/{{artwork_id}}",
            "detection_results": f"{settings.API_V1_STR}/detection-results/{{artwork_id}}",
            "block_organization": f"{settings.API_V1_STR}/api-gate/block",
            "check_access": f"{settings.API_V1_STR}/api-gate/check",
            "statistics": f"{settings.API_V1_STR}/statistics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
