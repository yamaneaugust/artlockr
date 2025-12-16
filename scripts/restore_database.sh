#!/bin/bash
# Database restore script for ArtLockr
#
# This script restores a PostgreSQL database dump
# and restores the data directory from backup
#
# Usage:
#   ./scripts/restore_database.sh <backup_name>

set -e  # Exit on error

# Configuration
DB_NAME="artlockr_db"
DB_USER="artlockr"
BACKUP_DIR="data/backups"

# Check if backup name provided
if [ -z "$1" ]; then
    echo "❌ Error: No backup name provided"
    echo ""
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"/*.dump 2>/dev/null | sed 's/.*\//  - /' | sed 's/.dump$//' || echo "  No backups found"
    exit 1
fi

BACKUP_NAME=$1

# Check if backup files exist
if [ ! -f "$BACKUP_DIR/${BACKUP_NAME}.dump" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_DIR/${BACKUP_NAME}.dump"
    exit 1
fi

echo "=========================================="
echo "ArtLockr Database Restore"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will REPLACE the current database!"
echo "   Database: $DB_NAME"
echo "   Backup: $BACKUP_NAME"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Drop and recreate database
echo "Dropping existing database..."
dropdb -U "$DB_USER" --if-exists "$DB_NAME"
echo "✓ Database dropped"

echo "Creating new database..."
createdb -U "$DB_USER" "$DB_NAME"
echo "✓ Database created"

# Restore PostgreSQL dump
echo ""
echo "Restoring database from backup..."
pg_restore -U "$DB_USER" -d "$DB_NAME" -v "$BACKUP_DIR/${BACKUP_NAME}.dump"
echo "✓ Database restored"

# Restore data directories if backup exists
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" ]; then
    echo ""
    echo "Restoring data directories..."

    # Backup current data (just in case)
    if [ -d "data/features" ] || [ -d "data/faiss_indexes" ]; then
        echo "  Creating safety backup of current data..."
        SAFETY_BACKUP="data/backups/pre_restore_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$SAFETY_BACKUP"
        [ -d "data/features" ] && cp -r data/features "$SAFETY_BACKUP/" 2>/dev/null || true
        [ -d "data/faiss_indexes" ] && cp -r data/faiss_indexes "$SAFETY_BACKUP/" 2>/dev/null || true
        echo "  ✓ Safety backup created at: $SAFETY_BACKUP"
    fi

    # Extract data backup
    echo "  Extracting data archive..."
    tar -xzf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz"
    echo "  ✓ Data directories restored"
else
    echo ""
    echo "⚠️  Data archive not found, skipping data restore"
fi

# Verify restore
echo ""
echo "Verifying restore..."
TABLE_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
echo "  ✓ Found $TABLE_COUNT tables"

echo ""
echo "=========================================="
echo "✓ Restore complete!"
echo "=========================================="
echo ""
echo "Restored from: $BACKUP_NAME"
echo "Database: $DB_NAME"
echo ""

# Show manifest if it exists
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt" ]; then
    echo "Backup manifest:"
    cat "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt"
fi
