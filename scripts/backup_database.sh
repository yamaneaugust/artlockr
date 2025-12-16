#!/bin/bash
# Database backup script for ArtLockr
#
# This script creates a PostgreSQL dump of the database
# and backs up the data directory (features, indexes, etc.)
#
# Usage:
#   ./scripts/backup_database.sh [backup_name]

set -e  # Exit on error

# Configuration
DB_NAME="artlockr_db"
DB_USER="artlockr"
BACKUP_DIR="data/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME=${1:-"backup_${TIMESTAMP}"}

echo "=========================================="
echo "ArtLockr Database Backup"
echo "=========================================="
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
pg_dump -U "$DB_USER" -F c -b -v -f "$BACKUP_DIR/${BACKUP_NAME}.dump" "$DB_NAME"
echo "✓ Database dumped to: $BACKUP_DIR/${BACKUP_NAME}.dump"

# Backup data directories
echo ""
echo "Backing up data directories..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" \
    data/features \
    data/faiss_indexes \
    2>/dev/null || echo "⚠️  Some directories may not exist yet"

echo "✓ Data archived to: $BACKUP_DIR/${BACKUP_NAME}_data.tar.gz"

# Create backup manifest
echo ""
echo "Creating backup manifest..."
cat > "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt" << EOF
ArtLockr Backup Manifest
========================
Backup Name: $BACKUP_NAME
Created: $(date)
Database: $DB_NAME
Files:
  - ${BACKUP_NAME}.dump (PostgreSQL dump)
  - ${BACKUP_NAME}_data.tar.gz (Data directories)

To restore this backup:
  ./scripts/restore_database.sh $BACKUP_NAME
EOF

echo "✓ Manifest created: $BACKUP_DIR/${BACKUP_NAME}_manifest.txt"

# Calculate sizes
echo ""
echo "Backup Summary:"
echo "----------------------------------------"
if [ -f "$BACKUP_DIR/${BACKUP_NAME}.dump" ]; then
    DB_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.dump" | cut -f1)
    echo "  Database dump: $DB_SIZE"
fi
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" ]; then
    DATA_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" | cut -f1)
    echo "  Data archive: $DATA_SIZE"
fi
echo "  Location: $BACKUP_DIR/"
echo "----------------------------------------"

echo ""
echo "✓ Backup complete: $BACKUP_NAME"
echo ""

# Optional: Clean up old backups (keep last 10)
echo "Cleaning up old backups (keeping last 10)..."
cd "$BACKUP_DIR"
ls -t backup_*.dump 2>/dev/null | tail -n +11 | xargs -r rm -f
ls -t backup_*_data.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
ls -t backup_*_manifest.txt 2>/dev/null | tail -n +11 | xargs -r rm -f
echo "✓ Cleanup complete"
