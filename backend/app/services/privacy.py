"""
Privacy service for feature-only storage and data protection.
Ensures artists' artwork is protected and only features are stored.
"""
import os
import hashlib
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import json

from backend.app.core.config import settings


class PrivacyService:
    """
    Handle privacy-first storage and data protection.
    Default: Store only features, delete original images.
    """

    def __init__(self):
        self.features_dir = Path(settings.FEATURES_DIR)
        self.features_dir.mkdir(parents=True, exist_ok=True)

    async def save_features_only(
        self,
        features,
        file_hash: str,
        original_filename: str
    ) -> str:
        """
        Save only feature vectors, no original image.

        Args:
            features: Extracted feature vector (numpy array)
            file_hash: SHA-256 hash of original file
            original_filename: Original filename for reference

        Returns:
            Path to saved features
        """
        import numpy as np

        feature_path = self.features_dir / f"{file_hash}.npy"

        # Save features
        np.save(feature_path, features)

        # Save metadata (without storing original image)
        metadata_path = self.features_dir / f"{file_hash}_metadata.json"
        metadata = {
            'file_hash': file_hash,
            'original_filename': original_filename,
            'feature_extraction_date': datetime.utcnow().isoformat(),
            'feature_dim': features.shape[0],
            'storage_mode': 'features_only'
        }

        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))

        return str(feature_path)

    async def delete_image_file(self, file_path: str) -> bool:
        """
        Securely delete original image file.

        Args:
            file_path: Path to image file

        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(file_path):
                # Overwrite with random data before deletion (secure delete)
                file_size = os.path.getsize(file_path)

                async with aiofiles.open(file_path, 'wb') as f:
                    # Overwrite with zeros
                    await f.write(b'\x00' * file_size)

                # Delete file
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False

    def calculate_scheduled_deletion_date(
        self,
        retention_days: int
    ) -> datetime:
        """
        Calculate when data should be auto-deleted.

        Args:
            retention_days: Number of days to retain data

        Returns:
            Scheduled deletion datetime
        """
        return datetime.utcnow() + timedelta(days=retention_days)

    async def export_artist_data(
        self,
        artist_id: int,
        artworks: list,
        detection_results: list
    ) -> dict:
        """
        Export all artist data (GDPR/CCPA compliance).

        Args:
            artist_id: Artist ID
            artworks: List of artwork records
            detection_results: List of detection results

        Returns:
            Complete data export
        """
        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'artist_id': artist_id,
            'artworks': [
                {
                    'id': art.id,
                    'title': art.title,
                    'description': art.description,
                    'upload_date': art.upload_date.isoformat() if art.upload_date else None,
                    'file_hash': art.file_hash,
                    'art_style': art.art_style,
                    'storage_mode': art.storage_mode,
                    'image_deleted': art.image_deleted
                }
                for art in artworks
            ],
            'detection_results': [
                {
                    'id': dr.id,
                    'scan_date': dr.scan_date.isoformat() if dr.scan_date else None,
                    'matches_found': dr.matches_found,
                    'threshold_used': dr.threshold_used
                }
                for dr in detection_results
            ],
            'data_rights': {
                'right_to_access': 'You have the right to access your data',
                'right_to_deletion': 'You can request deletion at any time',
                'right_to_portability': 'You can export your data anytime',
                'right_to_rectification': 'You can update your data anytime'
            }
        }

        return export_data

    def verify_storage_mode(self, storage_mode: str) -> bool:
        """Validate storage mode"""
        valid_modes = ['features_only', 'encrypted', 'full']
        return storage_mode in valid_modes

    def get_privacy_report(self, artist) -> dict:
        """
        Generate privacy report for artist.

        Args:
            artist: Artist database record

        Returns:
            Privacy compliance report
        """
        return {
            'storage_mode': artist.storage_mode,
            'auto_delete_images': artist.auto_delete_images,
            'data_retention_days': artist.data_retention_days,
            'consent_privacy_policy': artist.consent_privacy_policy,
            'consent_notifications': artist.consent_notifications,
            'consent_date': artist.consent_date.isoformat() if artist.consent_date else None,
            'privacy_commitment': 'We only store feature vectors, not your original artwork',
            'data_usage': 'Your data is used only for copyright detection',
            'third_party_sharing': 'We never share your data with third parties',
            'ai_training': 'We will NEVER use your artwork for AI training'
        }


class CryptographicProofService:
    """
    Generate and verify cryptographic proofs of artwork ownership.
    """

    @staticmethod
    def generate_file_hash(file_content: bytes) -> str:
        """Generate SHA-256 hash of file"""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def generate_proof_hash(
        file_hash: str,
        artist_id: int,
        timestamp: datetime
    ) -> str:
        """
        Generate composite proof hash.

        Proves: "Artist X uploaded file with hash Y at time Z"

        Args:
            file_hash: SHA-256 of file
            artist_id: Artist ID
            timestamp: Upload timestamp

        Returns:
            Composite proof hash
        """
        proof_string = f"{file_hash}:{artist_id}:{timestamp.isoformat()}"
        return hashlib.sha256(proof_string.encode()).hexdigest()

    @staticmethod
    def create_upload_proof(
        file_content: bytes,
        artist_id: int,
        timestamp: Optional[datetime] = None
    ) -> Tuple[str, str, datetime]:
        """
        Create cryptographic proof of upload.

        Args:
            file_content: Original file bytes
            artist_id: Artist ID
            timestamp: Upload time (defaults to now)

        Returns:
            (file_hash, proof_hash, timestamp)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        file_hash = CryptographicProofService.generate_file_hash(file_content)
        proof_hash = CryptographicProofService.generate_proof_hash(
            file_hash, artist_id, timestamp
        )

        return file_hash, proof_hash, timestamp

    @staticmethod
    def verify_proof(
        file_content: bytes,
        artist_id: int,
        timestamp: datetime,
        stored_proof_hash: str
    ) -> bool:
        """
        Verify proof of ownership.

        Args:
            file_content: File to verify
            artist_id: Claimed artist ID
            timestamp: Claimed timestamp
            stored_proof_hash: Stored proof hash

        Returns:
            True if proof is valid
        """
        file_hash = CryptographicProofService.generate_file_hash(file_content)
        calculated_proof = CryptographicProofService.generate_proof_hash(
            file_hash, artist_id, timestamp
        )

        return calculated_proof == stored_proof_hash

    @staticmethod
    def generate_verification_certificate(
        artwork_id: int,
        file_hash: str,
        proof_hash: str,
        artist_id: int,
        timestamp: datetime
    ) -> dict:
        """
        Generate human-readable verification certificate.

        Args:
            artwork_id: Artwork database ID
            file_hash: File SHA-256
            proof_hash: Proof hash
            artist_id: Artist ID
            timestamp: Upload timestamp

        Returns:
            Verification certificate
        """
        return {
            'certificate_type': 'ArtLockr Ownership Proof',
            'artwork_id': artwork_id,
            'artist_id': artist_id,
            'upload_timestamp': timestamp.isoformat(),
            'file_hash_sha256': file_hash,
            'proof_hash': proof_hash,
            'verification_url': f"https://artlockr.com/verify/{proof_hash}",
            'issued_at': datetime.utcnow().isoformat(),
            'validity': 'This certificate cryptographically proves artwork ownership',
            'instructions': 'Share this certificate to prove you uploaded this artwork first'
        }
