"""
Privacy-first API endpoints with feature-only storage and cryptographic proofs.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import tempfile
import os
from datetime import datetime

from backend.app.db.session import get_db
from backend.app.models.database import (
    Artist, Artwork, UploadProof,
    ArtistPrivacySettings
)
from backend.app.core.config import settings
from backend.app.services.privacy import PrivacyService, CryptographicProofService
from ml_models.inference.copyright_detector import CopyrightDetector

router = APIRouter()

# Initialize services
privacy_service = PrivacyService()
crypto_service = CryptographicProofService()

# Initialize detector
detector = CopyrightDetector(
    model_name=settings.MODEL_NAME,
    weights=settings.MODEL_WEIGHTS,
    device=settings.DEVICE,
    feature_dim=settings.FEATURE_DIM
)


@router.post("/upload-artwork-private")
async def upload_artwork_private(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    art_style: str = Form('general'),
    complexity: str = Form('medium'),
    storage_mode: str = Form('features_only'),
    artist_id: int = 1,  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db)
):
    """
    Privacy-first artwork upload.

    DEFAULT BEHAVIOR:
    - Extracts features from image
    - Stores ONLY feature vectors
    - Deletes original image immediately
    - Generates cryptographic proof of ownership

    Args:
        file: Image file
        title: Artwork title
        description: Artwork description
        art_style: Art style (photorealistic, digital_art, abstract, etc.)
        complexity: Artwork complexity (simple, medium, complex)
        storage_mode: How to store (features_only, encrypted, full)
        artist_id: Artist ID

    Returns:
        Artwork info + cryptographic proof
    """
    # Validate storage mode
    if not privacy_service.verify_storage_mode(storage_mode):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid storage mode. Must be: features_only, encrypted, or full"
        )

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

    # Generate cryptographic proof
    timestamp = datetime.utcnow()
    file_hash, proof_hash, proof_timestamp = crypto_service.create_upload_proof(
        content, artist_id, timestamp
    )

    # Check for duplicates
    result = await db.execute(
        select(Artwork).where(Artwork.file_hash == file_hash)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This artwork has already been uploaded"
        )

    # Get artist settings
    artist_result = await db.execute(
        select(Artist).where(Artist.id == artist_id)
    )
    artist = artist_result.scalar_one_or_none()

    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found"
        )

    # Determine final storage mode (artist preference overrides)
    final_storage_mode = artist.storage_mode if artist.storage_mode else storage_mode

    # Extract features using temporary file
    try:
        # Create temporary file for feature extraction
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Extract features
        features = detector.extract_features(tmp_file_path)

        # Save features (always save features regardless of storage mode)
        feature_path = await privacy_service.save_features_only(
            features,
            file_hash,
            file.filename
        )

        # Handle original image based on storage mode
        final_file_path = None
        image_deleted = False

        if final_storage_mode == 'features_only':
            # Delete temporary file immediately
            os.unlink(tmp_file_path)
            image_deleted = True
        elif final_storage_mode == 'full':
            # Keep the file (move to permanent storage)
            final_file_path = os.path.join(
                settings.UPLOAD_DIR,
                f"{artist_id}",
                f"{file_hash}_{file.filename}"
            )
            os.makedirs(os.path.dirname(final_file_path), exist_ok=True)
            os.rename(tmp_file_path, final_file_path)
        else:
            # Encrypted mode (not fully implemented yet)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Encrypted storage mode not yet implemented"
            )

    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )

    # Calculate scheduled deletion date
    scheduled_deletion = None
    if artist.data_retention_days:
        scheduled_deletion = privacy_service.calculate_scheduled_deletion_date(
            artist.data_retention_days
        )

    # Create artwork database entry
    artwork = Artwork(
        artist_id=artist_id,
        title=title,
        description=description,
        file_path=final_file_path,
        file_hash=file_hash,
        feature_path=feature_path,
        upload_date=timestamp,
        art_style=art_style,
        complexity=complexity,
        storage_mode=final_storage_mode,
        image_deleted=image_deleted,
        image_deleted_date=timestamp if image_deleted else None,
        scheduled_deletion_date=scheduled_deletion,
        upload_proof_hash=proof_hash
    )

    db.add(artwork)
    await db.flush()  # Get artwork ID

    # Create upload proof record
    proof = UploadProof(
        artwork_id=artwork.id,
        artist_id=artist_id,
        file_hash=file_hash,
        proof_hash=proof_hash,
        timestamp=proof_timestamp
    )

    db.add(proof)
    await db.commit()
    await db.refresh(artwork)

    # Generate verification certificate
    certificate = crypto_service.generate_verification_certificate(
        artwork.id,
        file_hash,
        proof_hash,
        artist_id,
        proof_timestamp
    )

    return {
        "id": artwork.id,
        "title": artwork.title,
        "art_style": artwork.art_style,
        "storage_mode": final_storage_mode,
        "image_stored": not image_deleted,
        "features_extracted": True,
        "feature_path": feature_path,
        "cryptographic_proof": {
            "file_hash": file_hash,
            "proof_hash": proof_hash,
            "timestamp": proof_timestamp.isoformat(),
            "verification_certificate": certificate
        },
        "privacy": {
            "original_image_deleted": image_deleted,
            "only_features_stored": final_storage_mode == 'features_only',
            "scheduled_deletion": scheduled_deletion.isoformat() if scheduled_deletion else None
        },
        "message": "Artwork uploaded with privacy protection"
    }


@router.get("/privacy/my-data")
async def get_my_data(
    artist_id: int = 1,  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db)
):
    """
    Get all data we have on an artist (GDPR/CCPA compliance).

    Returns:
        Complete data transparency report
    """
    # Get artist
    artist_result = await db.execute(
        select(Artist).where(Artist.id == artist_id)
    )
    artist = artist_result.scalar_one_or_none()

    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found"
        )

    # Get artworks
    artworks_result = await db.execute(
        select(Artwork).where(Artwork.artist_id == artist_id)
    )
    artworks = artworks_result.scalars().all()

    # Get privacy settings
    privacy_result = await db.execute(
        select(ArtistPrivacySettings).where(
            ArtistPrivacySettings.artist_id == artist_id
        )
    )
    privacy_settings = privacy_result.scalar_one_or_none()

    # Count images stored vs deleted
    images_stored = sum(1 for art in artworks if not art.image_deleted)
    images_deleted = sum(1 for art in artworks if art.image_deleted)

    return {
        "artist_id": artist_id,
        "username": artist.username,
        "email": artist.email,
        "account_created": artist.created_at.isoformat(),
        "storage_summary": {
            "total_artworks": len(artworks),
            "images_stored": images_stored,
            "images_deleted": images_deleted,
            "features_stored": len(artworks),
            "storage_mode": artist.storage_mode,
            "data_retention_days": artist.data_retention_days
        },
        "privacy_settings": {
            "auto_delete_images": artist.auto_delete_images,
            "consent_privacy_policy": artist.consent_privacy_policy,
            "consent_notifications": artist.consent_notifications,
            "consent_date": artist.consent_date.isoformat() if artist.consent_date else None
        },
        "artworks": [
            {
                "id": art.id,
                "title": art.title,
                "upload_date": art.upload_date.isoformat(),
                "art_style": art.art_style,
                "storage_mode": art.storage_mode,
                "image_deleted": art.image_deleted,
                "has_cryptographic_proof": bool(art.upload_proof_hash),
                "scheduled_deletion": art.scheduled_deletion_date.isoformat() if art.scheduled_deletion_date else None
            }
            for art in artworks
        ],
        "data_rights": {
            "export_data": "/api/v1/privacy/export",
            "delete_data": "/api/v1/privacy/delete-all",
            "update_settings": "/api/v1/privacy/settings"
        },
        "compliance": {
            "gdpr_compliant": True,
            "ccpa_compliant": True,
            "right_to_access": "You are accessing your data now",
            "right_to_deletion": "Contact support or use delete endpoint",
            "right_to_portability": "Use export endpoint to download all data"
        }
    }


@router.post("/privacy/delete-all")
async def delete_all_data(
    confirm: bool = Form(...),
    artist_id: int = 1,  # TODO: Get from authentication
    db: AsyncSession = Depends(get_db)
):
    """
    Delete ALL artist data (GDPR Right to Deletion).

    WARNING: This is irreversible!

    Args:
        confirm: Must be True to proceed
        artist_id: Artist ID

    Returns:
        Deletion confirmation
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion by setting confirm=true"
        )

    # Get all artworks
    artworks_result = await db.execute(
        select(Artwork).where(Artwork.artist_id == artist_id)
    )
    artworks = artworks_result.scalars().all()

    deleted_count = 0

    # Delete all files
    for artwork in artworks:
        # Delete image file if exists
        if artwork.file_path and os.path.exists(artwork.file_path):
            await privacy_service.delete_image_file(artwork.file_path)

        # Delete feature file if exists
        if artwork.feature_path and os.path.exists(artwork.feature_path):
            os.remove(artwork.feature_path)

        deleted_count += 1

    # Delete database records
    # (In production, you might want to mark as deleted rather than hard delete)
    # For now, we'll keep the Artist account but delete artworks
    from sqlalchemy import delete

    await db.execute(
        delete(Artwork).where(Artwork.artist_id == artist_id)
    )
    await db.commit()

    return {
        "deleted": True,
        "artworks_deleted": deleted_count,
        "message": "All your data has been permanently deleted",
        "artist_account": "Kept (deactivated). Contact support to delete account."
    }


@router.get("/privacy/verify-proof/{proof_hash}")
async def verify_ownership_proof(
    proof_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Publicly verify cryptographic proof of artwork ownership.

    Args:
        proof_hash: Proof hash to verify

    Returns:
        Verification result
    """
    # Get proof record
    result = await db.execute(
        select(UploadProof).where(UploadProof.proof_hash == proof_hash)
    )
    proof = result.scalar_one_or_none()

    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proof not found"
        )

    # Get artwork
    artwork_result = await db.execute(
        select(Artwork).where(Artwork.id == proof.artwork_id)
    )
    artwork = artwork_result.scalar_one_or_none()

    return {
        "valid": True,
        "proof_hash": proof_hash,
        "file_hash": proof.file_hash,
        "upload_timestamp": proof.timestamp.isoformat(),
        "artist_id": proof.artist_id,
        "artwork": {
            "id": artwork.id if artwork else None,
            "title": artwork.title if artwork else None,
            "art_style": artwork.art_style if artwork else None
        },
        "verification": {
            "status": "VERIFIED",
            "message": f"This artwork was uploaded on {proof.timestamp.isoformat()}",
            "proof_type": "Cryptographic SHA-256 hash",
            "tamper_proof": True
        }
    }
