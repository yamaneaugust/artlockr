"""Add performance indexes for faster queries

Revision ID: 002
Revises: 001
Create Date: 2024-12-16 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite indexes for common query patterns

    # Artworks: User + created_at for recent artwork queries
    op.create_index(
        'ix_artworks_user_created',
        'artworks',
        ['user_id', 'created_at'],
        unique=False
    )

    # Artworks: Art style + complexity for threshold lookups
    op.create_index(
        'ix_artworks_style_complexity',
        'artworks',
        ['art_style', 'complexity'],
        unique=False
    )

    # Detection results: Artwork + is_match for filtering matches
    op.create_index(
        'ix_detection_artwork_match',
        'detection_results',
        ['artwork_id', 'is_match'],
        unique=False
    )

    # Detection results: Artwork + similarity for ordering by similarity
    op.create_index(
        'ix_detection_artwork_similarity',
        'detection_results',
        ['artwork_id', 'similarity_score'],
        unique=False
    )

    # Detection results: Created_at for time-based queries
    op.create_index(
        'ix_detection_created_at',
        'detection_results',
        ['detected_at'],
        unique=False
    )

    # AI Images: Source + discovered date for tracking
    op.create_index(
        'ix_ai_images_source_discovered',
        'ai_images',
        ['source_name', 'discovered_at'],
        unique=False
    )

    # Blocked orgs: User + org name for quick lookups
    op.create_index(
        'ix_blocked_orgs_user_org',
        'blocked_organizations',
        ['user_id', 'organization_name'],
        unique=True  # Prevent duplicate blocks
    )

    # Consent: User + type for consent lookups
    op.create_index(
        'ix_consent_user_type',
        'consent_records',
        ['user_id', 'consent_type'],
        unique=False
    )

    # Consent: Expires_at for cleanup queries
    op.create_index(
        'ix_consent_expires_at',
        'consent_records',
        ['expires_at'],
        unique=False
    )

    # Cookie preferences: User + category for quick lookups
    op.create_index(
        'ix_cookie_user_category',
        'cookie_preferences',
        ['user_id', 'category'],
        unique=True  # One preference per category per user
    )

    # Add GIN index for JSONB metrics (PostgreSQL-specific)
    op.execute("""
        CREATE INDEX ix_detection_metrics_gin
        ON detection_results USING GIN (metrics_json)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_detection_metrics_gin")

    op.drop_index('ix_cookie_user_category', table_name='cookie_preferences')
    op.drop_index('ix_consent_expires_at', table_name='consent_records')
    op.drop_index('ix_consent_user_type', table_name='consent_records')
    op.drop_index('ix_blocked_orgs_user_org', table_name='blocked_organizations')
    op.drop_index('ix_ai_images_source_discovered', table_name='ai_images')
    op.drop_index('ix_detection_created_at', table_name='detection_results')
    op.drop_index('ix_detection_artwork_similarity', table_name='detection_results')
    op.drop_index('ix_detection_artwork_match', table_name='detection_results')
    op.drop_index('ix_artworks_style_complexity', table_name='artworks')
    op.drop_index('ix_artworks_user_created', table_name='artworks')
