"""
Build FAISS index from AI-generated artwork for fast similarity search.

This script:
1. Scans AI-generated artwork directory
2. Extracts features using ResNet
3. Builds FAISS index
4. Saves index to disk

Usage:
    python scripts/build_faiss_index.py --source-dir data/ai_generated
    python scripts/build_faiss_index.py --index-type ivf --device cuda
"""
import sys
import os
from pathlib import Path
import argparse
import numpy as np
from tqdm import tqdm

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ml_models.inference.copyright_detector import CopyrightDetector
from backend.app.services.faiss_service import FAISSIndexManager
from backend.app.core.config import settings


def build_index(
    source_dir: str,
    index_name: str = 'ai_artwork',
    index_type: str = 'flat',
    metric: str = 'l2',
    device: str = 'cuda',
    batch_size: int = 32
):
    """
    Build FAISS index from artwork directory.

    Args:
        source_dir: Directory containing images
        index_name: Name for the index
        index_type: FAISS index type (flat, ivf, hnsw)
        metric: Distance metric (l2, ip)
        device: Device for feature extraction (cuda/cpu)
        batch_size: Batch size for feature extraction
    """
    print(f"\n{'='*60}")
    print(f"Building FAISS Index: {index_name}")
    print(f"{'='*60}")
    print(f"Source directory: {source_dir}")
    print(f"Index type: {index_type}")
    print(f"Metric: {metric}")
    print(f"Device: {device}")
    print(f"{'='*60}\n")

    # Initialize detector
    print("Initializing ResNet feature extractor...")
    detector = CopyrightDetector(
        model_name=settings.MODEL_NAME,
        weights=settings.MODEL_WEIGHTS,
        device=device,
        feature_dim=settings.FEATURE_DIM
    )

    # Get all images
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: Source directory not found: {source_dir}")
        print(f"\nPlease add AI-generated images to: {source_dir}")
        return

    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        image_files.extend(list(source_path.glob(f"**/*{ext}")))
        image_files.extend(list(source_path.glob(f"**/*{ext.upper()}")))

    if len(image_files) == 0:
        print(f"Error: No images found in {source_dir}")
        print("\nSupported formats: jpg, jpeg, png, webp")
        return

    print(f"Found {len(image_files)} images to index\n")

    # Extract features
    print("Extracting features...")
    features_list = []
    ids_list = []
    metadata_list = []

    for i, image_file in enumerate(tqdm(image_files, desc="Processing images")):
        try:
            # Extract features
            features = detector.extract_features(str(image_file))
            features_list.append(features)

            # Use file name as ID (can be changed to database ID)
            ids_list.append(i)

            # Store metadata
            metadata_list.append({
                'file_path': str(image_file),
                'file_name': image_file.name,
                'file_size': os.path.getsize(image_file)
            })

        except Exception as e:
            print(f"\nError processing {image_file}: {e}")
            continue

    if len(features_list) == 0:
        print("Error: No features extracted")
        return

    # Convert to numpy array
    features_array = np.array(features_list).astype('float32')
    print(f"\nExtracted features shape: {features_array.shape}")

    # Create index
    print(f"\nCreating FAISS index ({index_type})...")
    index_manager = FAISSIndexManager()

    index = index_manager.create_index(
        name=index_name,
        dimension=features_array.shape[1],
        index_type=index_type,
        metric=metric
    )

    # Add vectors to index
    print("Adding vectors to index...")
    index.add_vectors(
        vectors=features_array,
        ids=ids_list,
        metadata=metadata_list
    )

    # Save index
    print("\nSaving index to disk...")
    index_manager.save_index(index_name)

    # Print statistics
    stats = index.get_stats()
    print(f"\n{'='*60}")
    print("Index Statistics:")
    print(f"{'='*60}")
    print(f"Total vectors: {stats['total_vectors']}")
    print(f"Dimension: {stats['dimension']}")
    print(f"Index type: {stats['index_type']}")
    print(f"Metric: {stats['metric']}")
    print(f"Memory usage: {stats['memory_usage_mb']:.2f} MB")
    print(f"Index saved to: ml_models/indexes/{index_name}/")
    print(f"{'='*60}\n")

    # Test search
    print("Testing search performance...")
    import time

    test_vector = features_array[0]
    start_time = time.time()
    results, distances = index.search(test_vector, k=10)
    search_time = time.time() - start_time

    print(f"Search time: {search_time*1000:.3f}ms")
    print(f"Top 10 results: {results[:10]}")
    print(f"\n✅ Index built successfully!")


def rebuild_index(
    index_name: str = 'ai_artwork',
    source_dir: str = None
):
    """
    Rebuild existing index (useful after adding/removing images).

    Args:
        index_name: Name of index to rebuild
        source_dir: Source directory (defaults to settings)
    """
    if source_dir is None:
        source_dir = settings.AI_GENERATED_DIR

    print(f"Rebuilding index: {index_name}")
    build_index(source_dir=source_dir, index_name=index_name)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Build FAISS index from AI-generated artwork'
    )

    parser.add_argument(
        '--source-dir',
        type=str,
        default='data/ai_generated',
        help='Directory containing AI-generated images'
    )

    parser.add_argument(
        '--index-name',
        type=str,
        default='ai_artwork',
        help='Name for the index'
    )

    parser.add_argument(
        '--index-type',
        type=str,
        default='flat',
        choices=['flat', 'ivf', 'hnsw'],
        help='FAISS index type'
    )

    parser.add_argument(
        '--metric',
        type=str,
        default='l2',
        choices=['l2', 'ip'],
        help='Distance metric (l2=Euclidean, ip=inner product/cosine)'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='cuda',
        choices=['cuda', 'cpu'],
        help='Device for feature extraction'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for feature extraction'
    )

    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Rebuild existing index'
    )

    args = parser.parse_args()

    if args.rebuild:
        rebuild_index(args.index_name, args.source_dir)
    else:
        build_index(
            source_dir=args.source_dir,
            index_name=args.index_name,
            index_type=args.index_type,
            metric=args.metric,
            device=args.device,
            batch_size=args.batch_size
        )


if __name__ == "__main__":
    main()
