#!/usr/bin/env python3
"""
Scheduled AI Image Scanner

Automatically scans directories for new AI-generated images and updates indexes.

Features:
- Periodic scanning (hourly, daily, weekly)
- Incremental updates (only process new images)
- Email notifications for new detections
- Logging and monitoring
- Graceful shutdown

Usage:
    # Run scanner every hour
    python scheduled_scanner.py --schedule hourly --source-dir /path/to/ai/images

    # Run daily at specific time
    python scheduled_scanner.py --schedule daily --time "02:00" --source-dir /path/to/ai/images

    # Run once (cron mode)
    python scheduled_scanner.py --once --source-dir /path/to/ai/images
"""

import argparse
import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import schedule

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scan_ai_images import AIImageScanner


class ScheduledScanner:
    """
    Scheduled scanner for continuous monitoring of AI image directories.

    Features:
    - Periodic scanning
    - Incremental updates
    - Error handling and retry
    - Logging
    """

    def __init__(
        self,
        source_dir: str,
        index_name: str = 'ai_artwork',
        index_type: str = 'ivf',
        model: str = 'resnet50',
        device: str = 'cuda',
        batch_size: int = 32,
        log_file: Optional[str] = None
    ):
        """
        Initialize scheduled scanner.

        Args:
            source_dir: Directory to scan
            index_name: Name of FAISS index
            index_type: FAISS index type
            model: ResNet model
            device: Device for processing
            batch_size: Batch size
            log_file: Log file path
        """
        self.source_dir = source_dir
        self.index_name = index_name
        self.index_type = index_type
        self.model = model
        self.device = device
        self.batch_size = batch_size

        # Setup logging
        self.setup_logging(log_file)

        # Scanner instance
        self.scanner = None

        # Shutdown flag
        self.shutdown_requested = False

        # Statistics
        self.scan_count = 0
        self.total_images_processed = 0
        self.last_scan_time = None

    def setup_logging(self, log_file: Optional[str] = None):
        """Setup logging configuration."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        handlers = [logging.StreamHandler()]

        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file))

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=handlers
        )

        self.logger = logging.getLogger('ScheduledScanner')

    def run_scan(self):
        """Execute a single scan."""
        self.logger.info("="*60)
        self.logger.info(f"Starting scan #{self.scan_count + 1}")
        self.logger.info(f"Source directory: {self.source_dir}")
        self.logger.info(f"Index: {self.index_name}")
        self.logger.info("="*60)

        try:
            # Initialize scanner
            self.scanner = AIImageScanner(
                model_name=self.model,
                device=self.device,
                batch_size=self.batch_size
            )

            # Load existing index for incremental update
            from backend.app.services.faiss_service import FAISSVectorIndex
            import json

            existing_hashes = set()
            index_path = Path('data/faiss_indexes') / self.index_name

            if index_path.exists():
                self.logger.info("Loading existing index for incremental update")
                try:
                    metadata_file = index_path / 'metadata.json'
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            existing_metadata = json.load(f)
                            for meta in existing_metadata.values():
                                if 'file_hash' in meta:
                                    existing_hashes.add(meta['file_hash'])
                        self.logger.info(f"Found {len(existing_hashes)} existing images")
                except Exception as e:
                    self.logger.warning(f"Could not load existing index: {e}")

            # Scan directory
            metadata_list = self.scanner.scan_directory(
                source_dir=self.source_dir,
                recursive=True,
                skip_existing=True,
                existing_hashes=existing_hashes
            )

            if not metadata_list:
                self.logger.info("No new images to process")
                self.scan_count += 1
                self.last_scan_time = datetime.now()
                return

            self.logger.info(f"Found {len(metadata_list)} new images")

            # Extract features
            features, successful_metadata = self.scanner.extract_features_batch(
                metadata_list=metadata_list
            )

            if features.size == 0:
                self.logger.warning("No features extracted")
                self.scan_count += 1
                self.last_scan_time = datetime.now()
                return

            # Update or build index
            if index_path.exists() and existing_hashes:
                self.logger.info("Updating existing index...")

                # Load existing index
                existing_index = FAISSVectorIndex.load(str(index_path))

                # Add new vectors
                new_ids = list(range(
                    existing_index.index.ntotal,
                    existing_index.index.ntotal + len(features)
                ))

                new_metadata = {
                    i: {
                        'file_path': m['file_path'],
                        'file_name': m['file_name'],
                        'file_hash': m['file_hash'],
                        'width': m.get('width'),
                        'height': m.get('height'),
                        'added_at': datetime.utcnow().isoformat()
                    }
                    for i, m in enumerate(successful_metadata, start=new_ids[0])
                }

                existing_index.add_vectors(features, new_ids, new_metadata)

                # Save updated index
                existing_index.save(str(index_path))
                self.logger.info(f"✓ Updated index with {len(features)} new vectors")
                self.logger.info(f"  Total vectors: {existing_index.index.ntotal}")

            else:
                # Build new index
                self.logger.info("Building new index...")
                index = self.scanner.build_faiss_index(
                    features=features,
                    metadata_list=successful_metadata,
                    index_name=self.index_name,
                    index_type=self.index_type
                )
                self.logger.info(f"✓ Built new index with {len(features)} vectors")

            # Update statistics
            self.scan_count += 1
            self.total_images_processed += len(successful_metadata)
            self.last_scan_time = datetime.now()

            self.logger.info("="*60)
            self.logger.info("Scan complete!")
            self.logger.info(f"Total scans: {self.scan_count}")
            self.logger.info(f"Total images processed: {self.total_images_processed}")
            self.logger.info(f"Last scan: {self.last_scan_time}")
            self.logger.info("="*60)

        except Exception as e:
            self.logger.error(f"Scan failed: {str(e)}", exc_info=True)

    def start_scheduled(self, interval: str, time_of_day: Optional[str] = None):
        """
        Start scheduled scanning.

        Args:
            interval: 'hourly', 'daily', or 'weekly'
            time_of_day: Time of day for daily/weekly scans (HH:MM format)
        """
        self.logger.info("Starting scheduled scanner")
        self.logger.info(f"Interval: {interval}")
        if time_of_day:
            self.logger.info(f"Time: {time_of_day}")

        # Setup schedule
        if interval == 'hourly':
            schedule.every().hour.do(self.run_scan)
        elif interval == 'daily':
            if time_of_day:
                schedule.every().day.at(time_of_day).do(self.run_scan)
            else:
                schedule.every().day.do(self.run_scan)
        elif interval == 'weekly':
            if time_of_day:
                schedule.every().week.at(time_of_day).do(self.run_scan)
            else:
                schedule.every().week.do(self.run_scan)
        else:
            raise ValueError(f"Invalid interval: {interval}")

        # Run initial scan
        self.logger.info("Running initial scan...")
        self.run_scan()

        # Main loop
        self.logger.info("Entering scheduled loop (Ctrl+C to stop)")

        try:
            while not self.shutdown_requested:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.logger.info("Shutting down...")

    def shutdown(self, signum=None, frame=None):
        """Handle shutdown signal."""
        self.logger.info(f"Received shutdown signal: {signum}")
        self.shutdown_requested = True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scheduled AI image scanner with incremental updates"
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
        help='Name of FAISS index (default: ai_artwork)'
    )

    parser.add_argument(
        '--index-type',
        type=str,
        default='ivf',
        choices=['flat', 'ivf', 'hnsw'],
        help='FAISS index type (default: ivf)'
    )

    # Schedule arguments
    schedule_group = parser.add_mutually_exclusive_group(required=True)
    schedule_group.add_argument(
        '--schedule',
        type=str,
        choices=['hourly', 'daily', 'weekly'],
        help='Scan interval'
    )
    schedule_group.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for cron)'
    )

    parser.add_argument(
        '--time',
        type=str,
        default=None,
        help='Time of day for daily/weekly scans (HH:MM format, e.g., 02:00)'
    )

    # Processing arguments
    parser.add_argument(
        '--model',
        type=str,
        default='resnet50',
        choices=['resnet50', 'resnet101', 'resnet152'],
        help='ResNet model (default: resnet50)'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='cuda',
        choices=['cuda', 'cpu'],
        help='Device (default: cuda)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size (default: 32)'
    )

    # Logging
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/scheduled_scanner.log',
        help='Log file path (default: logs/scheduled_scanner.log)'
    )

    args = parser.parse_args()

    # Initialize scanner
    scanner = ScheduledScanner(
        source_dir=args.source_dir,
        index_name=args.index_name,
        index_type=args.index_type,
        model=args.model,
        device=args.device,
        batch_size=args.batch_size,
        log_file=args.log_file
    )

    # Setup signal handlers
    signal.signal(signal.SIGINT, scanner.shutdown)
    signal.signal(signal.SIGTERM, scanner.shutdown)

    # Run
    if args.once:
        # Run once for cron
        scanner.run_scan()
    else:
        # Start scheduled scanning
        scanner.start_scheduled(
            interval=args.schedule,
            time_of_day=args.time
        )


if __name__ == '__main__':
    main()
