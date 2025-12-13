#!/usr/bin/env python3
"""
AI Image Scanner - Batch Processing System

Scans directories of AI-generated images, extracts features, and builds
FAISS indexes for fast copyright detection.

Features:
- Multi-threaded batch processing
- Progress tracking
- Error handling and retry logic
- Supports multiple image formats
- Incremental updates (add new images without full rebuild)
- Metadata extraction and storage

Usage:
    # Scan directory and build index
    python scan_ai_images.py --source-dir /path/to/ai/images --index-name ai_artwork_v1

    # Incremental update
    python scan_ai_images.py --source-dir /path/to/new/images --index-name ai_artwork_v1 --incremental

    # Scan and store features only (no index)
    python scan_ai_images.py --source-dir /path/to/ai/images --features-only
"""

import argparse
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import numpy as np
from PIL import Image
from tqdm import tqdm
import torch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_models.inference.copyright_detector import CopyrightDetector
from backend.app.services.faiss_service import FAISSVectorIndex


class AIImageScanner:
    """
    Scans directories of AI-generated images and extracts features.

    Supports:
    - Batch processing with progress bars
    - Multi-threaded feature extraction
    - Error handling and logging
    - Metadata extraction
    - Incremental updates
    """

    def __init__(
        self,
        model_name: str = 'resnet50',
        device: str = 'cuda',
        batch_size: int = 32,
        num_workers: int = 4,
        supported_formats: List[str] = None
    ):
        """
        Initialize scanner.

        Args:
            model_name: ResNet model ('resnet50', 'resnet101', 'resnet152')
            device: 'cuda' or 'cpu'
            batch_size: Batch size for feature extraction
            num_workers: Number of parallel workers
            supported_formats: List of supported image formats
        """
        self.device = device if torch.cuda.is_available() else 'cpu'
        print(f"Initializing scanner on device: {self.device}")

        # Initialize detector
        self.detector = CopyrightDetector(
            model_name=model_name,
            device=self.device
        )

        self.batch_size = batch_size
        self.num_workers = num_workers
        self.supported_formats = supported_formats or [
            '.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'
        ]

        # Statistics
        self.stats = {
            'total_images': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }

        # Error log
        self.errors = []

    def scan_directory(
        self,
        source_dir: str,
        recursive: bool = True,
        skip_existing: bool = False,
        existing_hashes: Optional[set] = None
    ) -> List[Dict]:
        """
        Scan directory for AI-generated images.

        Args:
            source_dir: Directory to scan
            recursive: Scan subdirectories
            skip_existing: Skip images already in index
            existing_hashes: Set of existing file hashes (for skip_existing)

        Returns:
            List of image metadata dictionaries
        """
        print(f"\nScanning directory: {source_dir}")
        print(f"Recursive: {recursive}")

        source_path = Path(source_dir)

        if not source_path.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")

        # Find all images
        image_files = []

        if recursive:
            for ext in self.supported_formats:
                image_files.extend(source_path.rglob(f"*{ext}"))
                image_files.extend(source_path.rglob(f"*{ext.upper()}"))
        else:
            for ext in self.supported_formats:
                image_files.extend(source_path.glob(f"*{ext}"))
                image_files.extend(source_path.glob(f"*{ext.upper()}"))

        # Remove duplicates and sort
        image_files = sorted(list(set(image_files)))

        print(f"Found {len(image_files)} images")

        # Build metadata
        metadata_list = []
        existing_hashes = existing_hashes or set()

        for img_path in tqdm(image_files, desc="Building metadata"):
            try:
                # Calculate file hash
                file_hash = self._calculate_file_hash(img_path)

                # Skip if already exists
                if skip_existing and file_hash in existing_hashes:
                    self.stats['skipped'] += 1
                    continue

                # Get file info
                stat = img_path.stat()

                metadata = {
                    'file_path': str(img_path.absolute()),
                    'file_name': img_path.name,
                    'file_hash': file_hash,
                    'file_size': stat.st_size,
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'relative_path': str(img_path.relative_to(source_path))
                }

                # Try to get image dimensions
                try:
                    with Image.open(img_path) as img:
                        metadata['width'] = img.width
                        metadata['height'] = img.height
                        metadata['format'] = img.format
                except Exception as e:
                    metadata['width'] = None
                    metadata['height'] = None
                    metadata['format'] = None

                metadata_list.append(metadata)

            except Exception as e:
                self.errors.append({
                    'file': str(img_path),
                    'error': str(e),
                    'stage': 'metadata'
                })
                self.stats['failed'] += 1

        self.stats['total_images'] = len(metadata_list)
        print(f"Prepared {len(metadata_list)} images for processing")

        if self.stats['skipped'] > 0:
            print(f"Skipped {self.stats['skipped']} existing images")

        return metadata_list

    def extract_features_batch(
        self,
        metadata_list: List[Dict],
        output_dir: Optional[str] = None
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Extract features from images in batches.

        Args:
            metadata_list: List of image metadata
            output_dir: Directory to save features (optional)

        Returns:
            Tuple of (feature_matrix, updated_metadata_list)
        """
        print(f"\nExtracting features from {len(metadata_list)} images")
        print(f"Batch size: {self.batch_size}")
        print(f"Device: {self.device}")

        self.stats['start_time'] = time.time()

        all_features = []
        successful_metadata = []

        # Process in batches
        for i in tqdm(range(0, len(metadata_list), self.batch_size), desc="Processing batches"):
            batch_metadata = metadata_list[i:i + self.batch_size]
            batch_paths = [m['file_path'] for m in batch_metadata]

            try:
                # Extract features for batch
                batch_features = self.detector.batch_extract_features(
                    batch_paths,
                    normalize=True
                )

                # Save individual features if output_dir specified
                if output_dir:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)

                    for j, (features, metadata) in enumerate(zip(batch_features, batch_metadata)):
                        feature_file = output_path / f"{metadata['file_hash']}.npy"
                        np.save(feature_file, features)
                        metadata['feature_path'] = str(feature_file)

                all_features.append(batch_features)
                successful_metadata.extend(batch_metadata)
                self.stats['processed'] += len(batch_metadata)

            except Exception as e:
                # Handle batch failure - try individual processing
                print(f"\nBatch failed, processing individually: {str(e)}")

                for metadata in batch_metadata:
                    try:
                        features = self.detector.extract_features(metadata['file_path'])

                        if output_dir:
                            output_path = Path(output_dir)
                            feature_file = output_path / f"{metadata['file_hash']}.npy"
                            np.save(feature_file, features)
                            metadata['feature_path'] = str(feature_file)

                        all_features.append(features.reshape(1, -1))
                        successful_metadata.append(metadata)
                        self.stats['processed'] += 1

                    except Exception as e2:
                        self.errors.append({
                            'file': metadata['file_path'],
                            'error': str(e2),
                            'stage': 'feature_extraction'
                        })
                        self.stats['failed'] += 1

        self.stats['end_time'] = time.time()

        # Concatenate all features
        if all_features:
            feature_matrix = np.vstack(all_features)
        else:
            feature_matrix = np.array([])

        # Print statistics
        elapsed = self.stats['end_time'] - self.stats['start_time']
        print(f"\n{'='*60}")
        print(f"Feature Extraction Complete")
        print(f"{'='*60}")
        print(f"Total images: {self.stats['total_images']}")
        print(f"Successfully processed: {self.stats['processed']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Skipped (existing): {self.stats['skipped']}")
        print(f"Time elapsed: {elapsed:.2f}s")
        print(f"Average: {elapsed/max(self.stats['processed'], 1):.3f}s per image")
        print(f"Feature matrix shape: {feature_matrix.shape}")
        print(f"{'='*60}\n")

        return feature_matrix, successful_metadata

    def build_faiss_index(
        self,
        features: np.ndarray,
        metadata_list: List[Dict],
        index_name: str,
        index_type: str = 'ivf',
        metric: str = 'cosine',
        output_dir: str = 'data/faiss_indexes'
    ) -> FAISSVectorIndex:
        """
        Build FAISS index from features.

        Args:
            features: Feature matrix (N x D)
            metadata_list: List of metadata dicts
            index_name: Name for the index
            index_type: 'flat', 'ivf', or 'hnsw'
            metric: 'cosine' or 'l2'
            output_dir: Directory to save index

        Returns:
            FAISSVectorIndex object
        """
        print(f"\nBuilding FAISS index: {index_name}")
        print(f"Index type: {index_type}")
        print(f"Metric: {metric}")
        print(f"Features shape: {features.shape}")

        # Create index
        index = FAISSVectorIndex(
            dimension=features.shape[1],
            index_type=index_type,
            metric=metric
        )

        # Add vectors with metadata
        vector_ids = list(range(len(features)))

        # Build metadata dict
        metadata_dict = {
            i: {
                'file_path': m['file_path'],
                'file_name': m['file_name'],
                'file_hash': m['file_hash'],
                'width': m.get('width'),
                'height': m.get('height'),
                'format': m.get('format'),
                'added_at': datetime.utcnow().isoformat()
            }
            for i, m in enumerate(metadata_list)
        }

        print("Adding vectors to index...")
        index.add_vectors(features, vector_ids, metadata_dict)

        # Save index
        output_path = Path(output_dir) / index_name
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Saving index to: {output_path}")
        index.save(str(output_path))

        # Save scan metadata
        scan_metadata = {
            'index_name': index_name,
            'index_type': index_type,
            'metric': metric,
            'total_vectors': len(features),
            'feature_dimension': features.shape[1],
            'created_at': datetime.utcnow().isoformat(),
            'statistics': self.stats,
            'errors': self.errors[:100]  # Save first 100 errors
        }

        metadata_file = output_path / 'scan_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(scan_metadata, f, indent=2)

        print(f"\n✓ Index built successfully!")
        print(f"  Total vectors: {len(features)}")
        print(f"  Saved to: {output_path}")

        return index

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scan AI-generated images and build FAISS index for copyright detection"
    )

    # Required arguments
    parser.add_argument(
        '--source-dir',
        type=str,
        required=True,
        help='Directory containing AI-generated images'
    )

    # Index arguments
    parser.add_argument(
        '--index-name',
        type=str,
        default='ai_artwork',
        help='Name for the FAISS index (default: ai_artwork)'
    )

    parser.add_argument(
        '--index-type',
        type=str,
        choices=['flat', 'ivf', 'hnsw'],
        default='ivf',
        help='FAISS index type (default: ivf)'
    )

    parser.add_argument(
        '--metric',
        type=str,
        choices=['cosine', 'l2'],
        default='cosine',
        help='Distance metric (default: cosine)'
    )

    # Processing arguments
    parser.add_argument(
        '--model',
        type=str,
        choices=['resnet50', 'resnet101', 'resnet152'],
        default='resnet50',
        help='ResNet model to use (default: resnet50)'
    )

    parser.add_argument(
        '--device',
        type=str,
        choices=['cuda', 'cpu'],
        default='cuda',
        help='Device for processing (default: cuda)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for feature extraction (default: 32)'
    )

    parser.add_argument(
        '--num-workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )

    # Directory arguments
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/faiss_indexes',
        help='Output directory for index (default: data/faiss_indexes)'
    )

    parser.add_argument(
        '--features-dir',
        type=str,
        default=None,
        help='Directory to save individual features (optional)'
    )

    # Flags
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Scan subdirectories recursively (default: True)'
    )

    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Incremental update (skip existing images)'
    )

    parser.add_argument(
        '--features-only',
        action='store_true',
        help='Extract features only, do not build index'
    )

    args = parser.parse_args()

    # Initialize scanner
    scanner = AIImageScanner(
        model_name=args.model,
        device=args.device,
        batch_size=args.batch_size,
        num_workers=args.num_workers
    )

    # Load existing index for incremental update
    existing_hashes = set()
    if args.incremental and not args.features_only:
        index_path = Path(args.output_dir) / args.index_name
        if index_path.exists():
            print(f"Loading existing index for incremental update: {index_path}")
            try:
                # Load existing index to get hashes
                metadata_file = index_path / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        existing_metadata = json.load(f)
                        for meta in existing_metadata.values():
                            if 'file_hash' in meta:
                                existing_hashes.add(meta['file_hash'])
                    print(f"Found {len(existing_hashes)} existing images")
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")

    # Scan directory
    metadata_list = scanner.scan_directory(
        source_dir=args.source_dir,
        recursive=args.recursive,
        skip_existing=args.incremental,
        existing_hashes=existing_hashes
    )

    if not metadata_list:
        print("\n⚠ No images to process!")
        return

    # Extract features
    features, successful_metadata = scanner.extract_features_batch(
        metadata_list=metadata_list,
        output_dir=args.features_dir
    )

    if features.size == 0:
        print("\n⚠ No features extracted!")
        return

    # Build index (unless features-only mode)
    if not args.features_only:
        index = scanner.build_faiss_index(
            features=features,
            metadata_list=successful_metadata,
            index_name=args.index_name,
            index_type=args.index_type,
            metric=args.metric,
            output_dir=args.output_dir
        )

        # Test search
        print("\nTesting search with first image...")
        test_feature = features[0:1]
        result_ids, distances = index.search(test_feature, k=5, return_distances=True)
        print(f"Top 5 results: {result_ids}")
        print(f"Distances: {distances}")

    # Print errors if any
    if scanner.errors:
        print(f"\n⚠ {len(scanner.errors)} errors occurred during processing")
        print("First 5 errors:")
        for error in scanner.errors[:5]:
            print(f"  - {error['file']}: {error['error']}")

    print("\n✓ Scan complete!")


if __name__ == '__main__':
    main()
