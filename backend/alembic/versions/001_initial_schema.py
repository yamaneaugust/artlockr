"""Initial database schema for ArtLock

Revision ID: 001
Revises:
Create Date: 2024-12-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_artist', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Create artworks table
    op.create_table(
        'artworks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('file_hash', sa.String(), nullable=True),
        sa.Column('feature_vector_path', sa.String(), nullable=True),

        # Privacy fields (Iteration 1)
        sa.Column('art_style', sa.String(), nullable=True, server_default='general'),
        sa.Column('complexity', sa.String(), nullable=True, server_default='medium'),
        sa.Column('custom_threshold', sa.Float(), nullable=True),
        sa.Column('storage_mode', sa.String(), nullable=True, server_default='features_only'),
        sa.Column('image_deleted', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('upload_proof_hash', sa.String(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_artworks_id', 'artworks', ['id'], unique=False)
    op.create_index('ix_artworks_user_id', 'artworks', ['user_id'], unique=False)
    op.create_index('ix_artworks_file_hash', 'artworks', ['file_hash'], unique=True)
    op.create_index('ix_artworks_upload_proof_hash', 'artworks', ['upload_proof_hash'], unique=False)

    # Create ai_images table
    op.create_table(
        'ai_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('source_name', sa.String(), nullable=True),
        sa.Column('file_hash', sa.String(), nullable=True),
        sa.Column('feature_vector_path', sa.String(), nullable=True),
        sa.Column('generator_model', sa.String(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_images_id', 'ai_images', ['id'], unique=False)
    op.create_index('ix_ai_images_file_hash', 'ai_images', ['file_hash'], unique=True)
    op.create_index('ix_ai_images_source_name', 'ai_images', ['source_name'], unique=False)

    # Create detection_results table
    op.create_table(
        'detection_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('artwork_id', sa.Integer(), nullable=False),
        sa.Column('ai_image_id', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('is_match', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('detection_method', sa.String(), nullable=True),
        sa.Column('metrics_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['artwork_id'], ['artworks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_image_id'], ['ai_images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_detection_results_id', 'detection_results', ['id'], unique=False)
    op.create_index('ix_detection_results_artwork_id', 'detection_results', ['artwork_id'], unique=False)
    op.create_index('ix_detection_results_ai_image_id', 'detection_results', ['ai_image_id'], unique=False)
    op.create_index('ix_detection_results_is_match', 'detection_results', ['is_match'], unique=False)
    op.create_index('ix_detection_results_similarity_score', 'detection_results', ['similarity_score'], unique=False)

    # Create blocked_organizations table (Iteration 4)
    op.create_table(
        'blocked_organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_name', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('blocked_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_blocked_organizations_id', 'blocked_organizations', ['id'], unique=False)
    op.create_index('ix_blocked_organizations_user_id', 'blocked_organizations', ['user_id'], unique=False)
    op.create_index('ix_blocked_organizations_org_name', 'blocked_organizations', ['organization_name'], unique=False)

    # Create consent_records table (Iteration 5)
    op.create_table(
        'consent_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('consent_type', sa.String(), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_consent_records_id', 'consent_records', ['id'], unique=False)
    op.create_index('ix_consent_records_user_id', 'consent_records', ['user_id'], unique=False)
    op.create_index('ix_consent_records_consent_type', 'consent_records', ['consent_type'], unique=False)

    # Create cookie_preferences table (Iteration 5)
    op.create_table(
        'cookie_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cookie_preferences_id', 'cookie_preferences', ['id'], unique=False)
    op.create_index('ix_cookie_preferences_user_id', 'cookie_preferences', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cookie_preferences_user_id', table_name='cookie_preferences')
    op.drop_index('ix_cookie_preferences_id', table_name='cookie_preferences')
    op.drop_table('cookie_preferences')

    op.drop_index('ix_consent_records_consent_type', table_name='consent_records')
    op.drop_index('ix_consent_records_user_id', table_name='consent_records')
    op.drop_index('ix_consent_records_id', table_name='consent_records')
    op.drop_table('consent_records')

    op.drop_index('ix_blocked_organizations_org_name', table_name='blocked_organizations')
    op.drop_index('ix_blocked_organizations_user_id', table_name='blocked_organizations')
    op.drop_index('ix_blocked_organizations_id', table_name='blocked_organizations')
    op.drop_table('blocked_organizations')

    op.drop_index('ix_detection_results_similarity_score', table_name='detection_results')
    op.drop_index('ix_detection_results_is_match', table_name='detection_results')
    op.drop_index('ix_detection_results_ai_image_id', table_name='detection_results')
    op.drop_index('ix_detection_results_artwork_id', table_name='detection_results')
    op.drop_index('ix_detection_results_id', table_name='detection_results')
    op.drop_table('detection_results')

    op.drop_index('ix_ai_images_source_name', table_name='ai_images')
    op.drop_index('ix_ai_images_file_hash', table_name='ai_images')
    op.drop_index('ix_ai_images_id', table_name='ai_images')
    op.drop_table('ai_images')

    op.drop_index('ix_artworks_upload_proof_hash', table_name='artworks')
    op.drop_index('ix_artworks_file_hash', table_name='artworks')
    op.drop_index('ix_artworks_user_id', table_name='artworks')
    op.drop_index('ix_artworks_id', table_name='artworks')
    op.drop_table('artworks')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
