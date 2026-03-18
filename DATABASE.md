# ArtLock Database Documentation

Complete database setup, migration, and maintenance guide for ArtLock.

## Overview

ArtLock uses **PostgreSQL** as its primary database with **Alembic** for schema migrations. The database stores user accounts, artwork metadata, AI image data, detection results, and compliance records.

### Key Features

- **Privacy-First**: Features-only storage (no images stored)
- **Full Schema Migrations**: Alembic-managed version control
- **Performance Optimized**: Composite indexes for common queries
- **GDPR/CCPA Compliant**: Consent tracking and data export
- **Automated Backups**: Shell scripts for backup/restore

## Database Schema

### Tables

#### users
User accounts (artists and admins)
```sql
- id (PK)
- email (unique, indexed)
- name
- hashed_password
- is_active
- is_artist
- created_at, updated_at
```

#### artworks
Artist-uploaded artwork metadata
```sql
- id (PK)
- user_id (FK → users)
- title
- original_filename
- file_hash (unique, indexed)
- feature_vector_path
- art_style (indexed)
- complexity
- custom_threshold
- storage_mode
- image_deleted
- upload_proof_hash (indexed)
- created_at, updated_at
```

#### ai_images
AI-generated images found online
```sql
- id (PK)
- source_url
- source_name (indexed)
- file_hash (unique, indexed)
- feature_vector_path
- generator_model
- discovered_at, created_at
```

#### detection_results
Copyright detection matches
```sql
- id (PK)
- artwork_id (FK → artworks, indexed)
- ai_image_id (FK → ai_images, indexed)
- similarity_score (indexed)
- is_match (indexed)
- detection_method
- metrics_json (JSONB, GIN indexed)
- detected_at, created_at
```

#### blocked_organizations
Organizations blocked by artists
```sql
- id (PK)
- user_id (FK → users, indexed)
- organization_name (indexed)
- reason
- blocked_at, created_at
```

#### consent_records
GDPR/CCPA consent tracking
```sql
- id (PK)
- user_id (FK → users, indexed)
- consent_type (indexed)
- granted (boolean)
- version
- ip_address
- user_agent
- timestamp
- expires_at (indexed)
- created_at
```

#### cookie_preferences
Cookie consent preferences
```sql
- id (PK)
- user_id (FK → users, indexed)
- category
- enabled (boolean)
- timestamp, created_at
```

## Performance Indexes

Migration `002_add_performance_indexes.py` adds composite indexes:

### Common Query Patterns
```sql
-- User's recent artworks
ix_artworks_user_created (user_id, created_at)

-- Art style threshold lookups
ix_artworks_style_complexity (art_style, complexity)

-- Detection matches for artwork
ix_detection_artwork_match (artwork_id, is_match)

-- Detection results by similarity
ix_detection_artwork_similarity (artwork_id, similarity_score)

-- Time-based detection queries
ix_detection_created_at (detected_at)

-- AI image source tracking
ix_ai_images_source_discovered (source_name, discovered_at)

-- Organization blocking (unique per user)
ix_blocked_orgs_user_org (user_id, organization_name) UNIQUE

-- Consent lookups
ix_consent_user_type (user_id, consent_type)
ix_consent_expires_at (expires_at)

-- Cookie preferences (unique per category)
ix_cookie_user_category (user_id, category) UNIQUE

-- JSONB metrics search (PostgreSQL-specific)
ix_detection_metrics_gin ON detection_results USING GIN (metrics_json)
```

## Setup and Installation

### Prerequisites

- PostgreSQL 12+
- Python 3.10+
- psycopg2-binary
- alembic

### Installation

```bash
# Install database dependencies
pip install psycopg2-binary alembic

# Configure database connection
# Edit backend/app/core/config.py or set environment variable:
export DATABASE_URL="postgresql://artlockr:password@localhost/artlockr_db"
```

### Initialize Database

Run the comprehensive initialization script:

```bash
# Basic initialization (creates DB, runs migrations, creates directories)
python scripts/init_database.py

# With sample seed data for testing
python scripts/init_database.py --seed-data

# Force recreate (WARNING: deletes all data)
python scripts/init_database.py --force
```

This script:
1. Creates PostgreSQL database if it doesn't exist
2. Runs all Alembic migrations
3. Creates storage directories (data/features, data/faiss_indexes, etc.)
4. Verifies all tables were created
5. Optionally loads seed data

## Migrations

### Alembic Configuration

Configuration is in `backend/alembic.ini` and `backend/alembic/env.py`.

### Available Migrations

1. **001_initial_schema.py**: Creates all tables with foreign keys and indexes
2. **002_add_performance_indexes.py**: Adds composite indexes for query performance

### Run Migrations

```bash
# Change to backend directory
cd backend

# Upgrade to latest version
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show migration history
alembic history

# Show current version
alembic current
```

### Create New Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration
alembic revision -m "description of changes"

# Edit the generated file in backend/alembic/versions/
# Then run: alembic upgrade head
```

## Seed Data

Load sample data for development/testing:

```bash
python scripts/seed_database.py
```

This creates:
- 3 users (2 artists, 1 admin)
- 3 sample artworks
- 2 AI images
- 2 detection results with multi-metric scores

**Test Accounts:**
- Artist 1: `artist1@example.com` / `password`
- Artist 2: `artist2@example.com` / `password`
- Admin: `admin@example.com` / `password`

## Backup and Restore

### Create Backup

```bash
# Automatic timestamped backup
./scripts/backup_database.sh

# Named backup
./scripts/backup_database.sh my_backup_name
```

Creates:
- `backup_name.dump` - PostgreSQL database dump
- `backup_name_data.tar.gz` - Data directories (features, indexes)
- `backup_name_manifest.txt` - Backup metadata

Backups are stored in `data/backups/` and automatically cleaned (keeps last 10).

### Restore Backup

```bash
# List available backups
ls -1 data/backups/*.dump

# Restore specific backup
./scripts/restore_database.sh backup_20241216_120000
```

⚠️ **WARNING**: Restore will DROP the existing database and recreate it!

## Maintenance

### Database Queries

```bash
# Connect to database
psql -U artlockr -d artlockr_db

# Common queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM artworks;
SELECT COUNT(*) FROM detection_results WHERE is_match = true;
SELECT art_style, COUNT(*) FROM artworks GROUP BY art_style;
```

### Vacuum and Analyze

```bash
# Connect and run maintenance
psql -U artlockr -d artlockr_db -c "VACUUM ANALYZE;"
```

### Index Statistics

```sql
-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Database Size

```sql
-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql://user:password@host:port/database

# Example for development
DATABASE_URL=postgresql://artlockr:artlockr_password@localhost/artlockr_db

# Example for production (use secrets management)
DATABASE_URL=postgresql://artlockr:${DB_PASSWORD}@db.example.com:5432/artlockr_production
```

## Production Considerations

### Security

1. **Use Strong Passwords**: Generate cryptographically secure passwords
2. **SSL/TLS Connections**: Enable SSL in production
   ```
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
   ```
3. **Connection Pooling**: Use pgBouncer or SQLAlchemy pooling
4. **Firewall Rules**: Restrict database access to application servers only

### Performance

1. **Regular VACUUM**: Schedule weekly `VACUUM ANALYZE`
2. **Index Monitoring**: Check `pg_stat_user_indexes` monthly
3. **Connection Limits**: Configure `max_connections` based on load
4. **Prepared Statements**: SQLAlchemy uses these by default

### Backup Strategy

1. **Daily Automated Backups**: Schedule `backup_database.sh` via cron
2. **Off-Site Storage**: Copy backups to S3/Azure/GCS
3. **Test Restores**: Monthly restore tests to verify backups
4. **Point-in-Time Recovery**: Enable PostgreSQL WAL archiving

### Monitoring

1. **Slow Query Log**: Enable logging for queries > 1 second
2. **Connection Monitoring**: Track active connections
3. **Disk Space**: Alert when database disk usage > 80%
4. **Replication Lag**: If using replication, monitor lag

## Troubleshooting

### Migration Failures

```bash
# Check current version
cd backend && alembic current

# Show migration history
alembic history

# Manually mark version (use with caution)
alembic stamp head
```

### Connection Issues

```bash
# Test connection
psql -U artlockr -d artlockr_db -c "SELECT 1;"

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Lock Issues

```sql
-- View active locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Kill blocking queries (careful!)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'artlockr_db' AND state = 'idle in transaction';
```

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

## Support

For database-related issues:
1. Check migration status: `alembic current`
2. Review logs: `backend/logs/`
3. Verify connection: `psql -U artlockr -d artlockr_db`
4. Check disk space: `df -h`
