#!/usr/bin/env python3
"""
Database initialization script for ArtLockr.

This script:
1. Creates the PostgreSQL database if it doesn't exist
2. Runs Alembic migrations to create all tables
3. Creates necessary directories
4. Initializes FAISS indexes
5. Optionally loads seed data

Usage:
    python scripts/init_database.py [--seed-data] [--force]

Options:
    --seed-data     Load sample seed data for testing
    --force         Drop existing database and recreate (WARNING: destroys data)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from backend.app.core.config import settings


def parse_database_url(url: str) -> dict:
    """Parse PostgreSQL database URL into components."""
    # Format: postgresql://user:password@host:port/database
    url = url.replace('postgresql://', '')
    auth, rest = url.split('@')
    user, password = auth.split(':')
    host_port, database = rest.split('/')

    if ':' in host_port:
        host, port = host_port.split(':')
    else:
        host = host_port
        port = '5432'

    return {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'database': database
    }


def create_database(force: bool = False):
    """Create the PostgreSQL database if it doesn't exist."""
    db_params = parse_database_url(settings.DATABASE_URL)

    print(f"Connecting to PostgreSQL server at {db_params['host']}:{db_params['port']}...")

    # Connect to PostgreSQL server (not specific database)
    try:
        conn = psycopg2.connect(
            user=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port'],
            database='postgres'  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_params['database'],)
        )
        exists = cursor.fetchone()

        if exists:
            if force:
                print(f"⚠️  Dropping existing database '{db_params['database']}'...")
                # Terminate all connections to the database
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_params['database']}'
                    AND pid <> pg_backend_pid()
                """)
                cursor.execute(f"DROP DATABASE {db_params['database']}")
                print(f"✓ Database '{db_params['database']}' dropped")
            else:
                print(f"✓ Database '{db_params['database']}' already exists")
                cursor.close()
                conn.close()
                return

        # Create database
        print(f"Creating database '{db_params['database']}'...")
        cursor.execute(f"CREATE DATABASE {db_params['database']}")
        print(f"✓ Database '{db_params['database']}' created successfully")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)


def run_migrations():
    """Run Alembic migrations to create database schema."""
    print("\nRunning database migrations...")

    try:
        # Change to backend directory where alembic.ini is located
        backend_dir = Path(__file__).parent.parent / 'backend'

        result = subprocess.run(
            ['alembic', 'upgrade', 'head'],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Migration failed:\n{result.stderr}")
            sys.exit(1)

        print("✓ Database migrations completed successfully")
        print(result.stdout)

    except FileNotFoundError:
        print("❌ Alembic not found. Install it with: pip install alembic")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        sys.exit(1)


def create_directories():
    """Create necessary directories for file storage."""
    print("\nCreating storage directories...")

    directories = [
        'data/uploads',
        'data/features',
        'data/ai_images',
        'data/faiss_indexes',
        'data/backups',
        'logs',
    ]

    for dir_path in directories:
        path = Path(__file__).parent.parent / dir_path
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {dir_path}")

    print("✓ Storage directories created")


def verify_database():
    """Verify database tables were created successfully."""
    print("\nVerifying database schema...")

    try:
        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            # Check if main tables exist
            tables = [
                'users',
                'artworks',
                'ai_images',
                'detection_results',
                'blocked_organizations',
                'consent_records',
                'cookie_preferences',
            ]

            for table in tables:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.scalar()

                if exists:
                    print(f"  ✓ Table '{table}' exists")
                else:
                    print(f"  ❌ Table '{table}' missing")

        print("✓ Database schema verification complete")

    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        sys.exit(1)


def load_seed_data():
    """Load sample seed data for testing."""
    print("\nLoading seed data...")

    try:
        # Run the seed script
        seed_script = Path(__file__).parent / 'seed_database.py'

        if not seed_script.exists():
            print("⚠️  Seed script not found, skipping...")
            return

        result = subprocess.run(
            [sys.executable, str(seed_script)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Seed data loading failed:\n{result.stderr}")
            return

        print("✓ Seed data loaded successfully")
        print(result.stdout)

    except Exception as e:
        print(f"⚠️  Error loading seed data: {e}")


def main():
    """Main initialization function."""
    parser = argparse.ArgumentParser(
        description='Initialize ArtLockr database'
    )
    parser.add_argument(
        '--seed-data',
        action='store_true',
        help='Load sample seed data for testing'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Drop existing database and recreate (WARNING: destroys data)'
    )

    args = parser.parse_args()

    if args.force:
        response = input(
            "⚠️  WARNING: This will DELETE all existing data. "
            "Are you sure? (yes/no): "
        )
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    print("=" * 60)
    print("ArtLockr Database Initialization")
    print("=" * 60)

    # Step 1: Create database
    create_database(force=args.force)

    # Step 2: Run migrations
    run_migrations()

    # Step 3: Create directories
    create_directories()

    # Step 4: Verify database
    verify_database()

    # Step 5: Load seed data (optional)
    if args.seed_data:
        load_seed_data()

    print("\n" + "=" * 60)
    print("✓ Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start the backend: cd backend && uvicorn app.main:app --reload")
    print("  2. Start the frontend: cd frontend && npm run dev")
    print("  3. Access the app at: http://localhost:3000")
    print()


if __name__ == '__main__':
    main()
