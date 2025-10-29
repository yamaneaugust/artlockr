from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import aiofiles
import hashlib
import os
from datetime import datetime

from backend.app.db.session import get_db
from backend.app.models.database import Artist, Artwork, DetectionResult, CopyrightMatch, APIGate, AccessLog
from backend.app.core.config import settings
from ml_models.inference.copyright_detector import CopyrightDetector

router = APIRouter()

# Initialize the copyright detector
detector = CopyrightDetector(
    model_name=settings.MODEL_NAME,
    weights=settings.MODEL_WEIGHTS,
    device=settings.DEVICE,
    feature_dim=settings.FEATURE_DIM
)


def compute_file_hash(file_content: bytes) -> str:
    """Compute SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to disk"""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    async with aiofiles.open(destination, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)
    return destination


@router.post("/upload-artwork")
async def upload_artwork(
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    artist_id: int = 1,  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db)
):
    """
    Upload original artwork for copyright protection.

    Args:
        file: Image file
        title: Artwork title
        description: Artwork description
        artist_id: Artist ID (from authentication)

    Returns:
        Artwork information including ID and feature extraction status
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
        )

    # Compute hash
    file_hash = compute_file_hash(content)

    # Check for duplicates
    existing = await db.execute(
        f"SELECT * FROM artworks WHERE file_hash = '{file_hash}'"
    )
    if existing.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This artwork has already been uploaded"
        )

    # Save file
    file_path = os.path.join(
        settings.UPLOAD_DIR,
        f"{artist_id}",
        f"{file_hash}_{file.filename}"
    )
    await file.seek(0)
    await save_upload_file(file, file_path)

    # Extract features
    try:
        features = detector.extract_features(file_path)
        feature_path = os.path.join(
            settings.FEATURES_DIR,
            f"{file_hash}.npy"
        )
        detector.save_features(features, feature_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting features: {str(e)}"
        )

    # Create database entry
    artwork = Artwork(
        artist_id=artist_id,
        title=title or file.filename,
        description=description,
        file_path=file_path,
        file_hash=file_hash,
        feature_path=feature_path,
        upload_date=datetime.utcnow()
    )

    db.add(artwork)
    await db.commit()
    await db.refresh(artwork)

    return {
        "id": artwork.id,
        "title": artwork.title,
        "file_path": artwork.file_path,
        "feature_extracted": True,
        "message": "Artwork uploaded successfully"
    }


@router.post("/detect-copyright/{artwork_id}")
async def detect_copyright(
    artwork_id: int,
    threshold: float = None,
    top_k: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect potential copyright infringement for a specific artwork.

    Args:
        artwork_id: ID of the original artwork
        threshold: Similarity threshold (0-1), defaults to config setting
        top_k: Number of top matches to return

    Returns:
        List of potential copyright infringements with similarity scores
    """
    # Get artwork from database
    result = await db.execute(
        f"SELECT * FROM artworks WHERE id = {artwork_id}"
    )
    artwork = result.first()

    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artwork not found"
        )

    # Use configured threshold if not provided
    if threshold is None:
        threshold = settings.SIMILARITY_THRESHOLD

    # Run copyright detection
    try:
        matches = detector.detect_copyright_infringement(
            original_image_path=artwork.file_path,
            ai_generated_images_dir=settings.AI_GENERATED_DIR,
            threshold=threshold,
            top_k=top_k
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during detection: {str(e)}"
        )

    # Save detection results to database
    detection_result = DetectionResult(
        artist_id=artwork.artist_id,
        artwork_id=artwork_id,
        scan_date=datetime.utcnow(),
        total_scanned=len(os.listdir(settings.AI_GENERATED_DIR)),
        matches_found=len(matches),
        threshold_used=threshold
    )

    db.add(detection_result)
    await db.commit()
    await db.refresh(detection_result)

    # Save individual matches
    for match in matches:
        copyright_match = CopyrightMatch(
            detection_result_id=detection_result.id,
            ai_artwork_path=match['image_path'],
            similarity_score=match['similarity_score'] / 100.0  # Convert back to 0-1
        )
        db.add(copyright_match)

    await db.commit()

    return {
        "detection_id": detection_result.id,
        "artwork_id": artwork_id,
        "matches_found": len(matches),
        "threshold": threshold,
        "matches": matches
    }


@router.get("/detection-results/{artwork_id}")
async def get_detection_results(
    artwork_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all detection results for a specific artwork.

    Args:
        artwork_id: ID of the artwork

    Returns:
        List of detection results
    """
    results = await db.execute(
        f"SELECT * FROM detection_results WHERE artwork_id = {artwork_id} ORDER BY scan_date DESC"
    )

    return {
        "artwork_id": artwork_id,
        "results": [dict(row) for row in results]
    }


@router.post("/api-gate/block")
async def block_organization(
    organization_name: str,
    organization_domain: str = None,
    reason: str = None,
    artist_id: int = 1,  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db)
):
    """
    Block an organization from accessing artist's artwork.

    Args:
        organization_name: Name of the organization to block
        organization_domain: Domain of the organization
        reason: Reason for blocking
        artist_id: Artist ID (from authentication)

    Returns:
        API gate information
    """
    api_gate = APIGate(
        artist_id=artist_id,
        organization_name=organization_name,
        organization_domain=organization_domain,
        is_blocked=True,
        block_reason=reason,
        blocked_date=datetime.utcnow()
    )

    db.add(api_gate)
    await db.commit()
    await db.refresh(api_gate)

    return {
        "id": api_gate.id,
        "organization_name": organization_name,
        "is_blocked": True,
        "message": f"Successfully blocked {organization_name}"
    }


@router.get("/api-gate/check")
async def check_access(
    request: Request,
    artwork_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if access to artwork is allowed based on API gating rules.

    Args:
        request: HTTP request
        artwork_id: ID of the artwork to access

    Returns:
        Access status
    """
    if not settings.ENABLE_API_GATING:
        return {"access_granted": True}

    # Get client information
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    # Get artwork
    artwork_result = await db.execute(
        f"SELECT * FROM artworks WHERE id = {artwork_id}"
    )
    artwork = artwork_result.first()

    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artwork not found"
        )

    # Check API gates
    gates_result = await db.execute(
        f"SELECT * FROM api_gates WHERE artist_id = {artwork.artist_id} AND is_blocked = TRUE"
    )

    access_granted = True
    blocked_by = None

    for gate in gates_result:
        # Check if request matches blocked organization
        if gate.organization_domain and gate.organization_domain in user_agent.lower():
            access_granted = False
            blocked_by = gate.organization_name
            break

    # Log access attempt
    access_log = AccessLog(
        api_gate_id=gate.id if not access_granted else None,
        ip_address=client_ip,
        user_agent=user_agent,
        requested_artwork_id=artwork_id,
        access_granted=access_granted,
        timestamp=datetime.utcnow()
    )

    db.add(access_log)
    await db.commit()

    if not access_granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Organization {blocked_by} is blocked by the artist."
        )

    return {
        "access_granted": True,
        "artwork_id": artwork_id
    }


@router.get("/statistics")
async def get_statistics(
    artist_id: int = 1,  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for an artist's copyright protection.

    Returns:
        Statistics including total artworks, detections, and matches found
    """
    artworks_result = await db.execute(
        f"SELECT COUNT(*) FROM artworks WHERE artist_id = {artist_id}"
    )
    total_artworks = artworks_result.scalar()

    detections_result = await db.execute(
        f"SELECT COUNT(*) FROM detection_results WHERE artist_id = {artist_id}"
    )
    total_detections = detections_result.scalar()

    matches_result = await db.execute(
        f"""
        SELECT COUNT(*) FROM copyright_matches cm
        JOIN detection_results dr ON cm.detection_result_id = dr.id
        WHERE dr.artist_id = {artist_id}
        """
    )
    total_matches = matches_result.scalar()

    gates_result = await db.execute(
        f"SELECT COUNT(*) FROM api_gates WHERE artist_id = {artist_id} AND is_blocked = TRUE"
    )
    blocked_orgs = gates_result.scalar()

    return {
        "total_artworks": total_artworks or 0,
        "total_detections": total_detections or 0,
        "total_matches_found": total_matches or 0,
        "blocked_organizations": blocked_orgs or 0
    }
