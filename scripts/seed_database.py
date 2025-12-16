#!/usr/bin/env python3
"""
Seed the database with sample data for testing.

This creates:
- Sample users (artists and admins)
- Sample artworks
- Sample AI images
- Sample detection results
- Sample consent records
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.database import (
    User,
    Artwork,
    AIImage,
    DetectionResult,
    Base
)
from backend.app.core.config import settings
import json


def seed_database():
    """Seed database with sample data."""
    print("Seeding database with sample data...")

    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Create sample users
        print("Creating sample users...")

        users = [
            User(
                email="artist1@example.com",
                name="Alice Artist",
                hashed_password="$2b$12$KIXxkCc5YThqmDqzYhH4l.example",  # Mock hash
                is_active=True,
                is_artist=True,
                created_at=datetime.utcnow()
            ),
            User(
                email="artist2@example.com",
                name="Bob Creator",
                hashed_password="$2b$12$KIXxkCc5YThqmDqzYhH4l.example",
                is_active=True,
                is_artist=True,
                created_at=datetime.utcnow()
            ),
            User(
                email="admin@example.com",
                name="Admin User",
                hashed_password="$2b$12$KIXxkCc5YThqmDqzYhH4l.example",
                is_active=True,
                is_artist=False,
                created_at=datetime.utcnow()
            ),
        ]

        for user in users:
            session.add(user)

        session.commit()
        print(f"  ✓ Created {len(users)} users")

        # Create sample artworks
        print("Creating sample artworks...")

        artworks = [
            Artwork(
                user_id=1,
                title="Sunset Landscape",
                original_filename="sunset_landscape.jpg",
                file_hash="abc123def456",
                feature_vector_path="data/features/abc123def456.npy",
                art_style="photorealistic",
                complexity="complex",
                storage_mode="features_only",
                image_deleted=True,
                upload_proof_hash="proof_abc123",
                created_at=datetime.utcnow() - timedelta(days=30)
            ),
            Artwork(
                user_id=1,
                title="Abstract Portrait",
                original_filename="abstract_portrait.png",
                file_hash="xyz789ghi012",
                feature_vector_path="data/features/xyz789ghi012.npy",
                art_style="abstract",
                complexity="medium",
                storage_mode="features_only",
                image_deleted=True,
                upload_proof_hash="proof_xyz789",
                created_at=datetime.utcnow() - timedelta(days=15)
            ),
            Artwork(
                user_id=2,
                title="Digital Illustration",
                original_filename="digital_art.jpg",
                file_hash="mno345pqr678",
                feature_vector_path="data/features/mno345pqr678.npy",
                art_style="digital_art",
                complexity="complex",
                storage_mode="features_only",
                image_deleted=True,
                upload_proof_hash="proof_mno345",
                created_at=datetime.utcnow() - timedelta(days=5)
            ),
        ]

        for artwork in artworks:
            session.add(artwork)

        session.commit()
        print(f"  ✓ Created {len(artworks)} artworks")

        # Create sample AI images
        print("Creating sample AI images...")

        ai_images = [
            AIImage(
                source_url="https://midjourney.com/gallery/image1",
                source_name="MidJourney Gallery",
                file_hash="ai_img_001",
                feature_vector_path="data/features/ai_img_001.npy",
                generator_model="MidJourney v6",
                discovered_at=datetime.utcnow() - timedelta(days=2),
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            AIImage(
                source_url="https://stablediffusion.com/gallery/image1",
                source_name="Stable Diffusion Community",
                file_hash="ai_img_002",
                feature_vector_path="data/features/ai_img_002.npy",
                generator_model="Stable Diffusion XL",
                discovered_at=datetime.utcnow() - timedelta(days=1),
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
        ]

        for ai_image in ai_images:
            session.add(ai_image)

        session.commit()
        print(f"  ✓ Created {len(ai_images)} AI images")

        # Create sample detection results
        print("Creating sample detection results...")

        detection_results = [
            DetectionResult(
                artwork_id=1,
                ai_image_id=1,
                similarity_score=0.94,
                is_match=True,
                detection_method="multi_metric",
                metrics_json=json.dumps({
                    "cosine": 0.92,
                    "ssim": 0.95,
                    "perceptual": 0.93,
                    "color_hist": 0.96,
                    "multi_layer": 0.94,
                    "fused": 0.94
                }),
                detected_at=datetime.utcnow() - timedelta(hours=12),
                created_at=datetime.utcnow() - timedelta(hours=12)
            ),
            DetectionResult(
                artwork_id=2,
                ai_image_id=2,
                similarity_score=0.87,
                is_match=True,
                detection_method="multi_metric",
                metrics_json=json.dumps({
                    "cosine": 0.85,
                    "ssim": 0.88,
                    "perceptual": 0.86,
                    "color_hist": 0.89,
                    "multi_layer": 0.87,
                    "fused": 0.87
                }),
                detected_at=datetime.utcnow() - timedelta(hours=6),
                created_at=datetime.utcnow() - timedelta(hours=6)
            ),
        ]

        for result in detection_results:
            session.add(result)

        session.commit()
        print(f"  ✓ Created {len(detection_results)} detection results")

        print("\n✓ Database seeding complete!")
        print("\nSample accounts:")
        print("  Artist 1: artist1@example.com / password")
        print("  Artist 2: artist2@example.com / password")
        print("  Admin:    admin@example.com / password")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    seed_database()
