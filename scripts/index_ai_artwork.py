"""
Index AI-generated artwork from a directory for comparison.
This script extracts features from all images in the AI_GENERATED_DIR
and saves them for fast comparison.
"""
import sys
import os
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_models.inference.copyright_detector import CopyrightDetector
from backend.app.core.config import settings


def index_ai_artwork(
    source_dir: str = None,
    batch_size: int = 32,
    device: str = "cuda"
):
    """
    Index AI-generated artwork from a directory.

    Args:
        source_dir: Directory containing AI-generated images
        batch_size: Batch size for processing
        device: Device to use (cuda or cpu)
    """
    if source_dir is None:
        source_dir = settings.AI_GENERATED_DIR

    print(f"Indexing AI-generated artwork from: {source_dir}")
    print(f"Using device: {device}")
    print(f"Batch size: {batch_size}")

    # Initialize detector
    detector = CopyrightDetector(
        model_name=settings.MODEL_NAME,
        weights=settings.MODEL_WEIGHTS,
        device=device,
        feature_dim=settings.FEATURE_DIM
    )

    # Get all image files
    source_path = Path(source_dir)
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        image_files.extend(list(source_path.glob(f"**/*{ext}")))
        image_files.extend(list(source_path.glob(f"**/*{ext.upper()}")))

    print(f"Found {len(image_files)} images to index")

    if len(image_files) == 0:
        print("No images found. Please add AI-generated images to the directory.")
        print(f"Directory: {source_dir}")
        return

    # Extract and save features
    indexed_count = 0
    for i, image_file in enumerate(image_files):
        try:
            # Extract features
            features = detector.extract_features(str(image_file))

            # Save features
            feature_filename = f"{image_file.stem}.npy"
            feature_path = os.path.join(settings.FEATURES_DIR, feature_filename)
            detector.save_features(features, feature_path)

            indexed_count += 1

            if (i + 1) % 10 == 0:
                print(f"Indexed {i + 1}/{len(image_files)} images...")

        except Exception as e:
            print(f"Error processing {image_file}: {e}")
            continue

    print(f"\nIndexing complete!")
    print(f"Successfully indexed: {indexed_count}/{len(image_files)} images")
    print(f"Features saved to: {settings.FEATURES_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index AI-generated artwork")
    parser.add_argument(
        "--source-dir",
        type=str,
        default=None,
        help="Directory containing AI-generated images"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for processing"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to use for inference"
    )

    args = parser.parse_args()

    index_ai_artwork(
        source_dir=args.source_dir,
        batch_size=args.batch_size,
        device=args.device
    )
