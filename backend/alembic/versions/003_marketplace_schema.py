"""Marketplace schema – replaces copyright-detection tables with
artist/company marketplace, creative works, listings, purchases, and
public dataset catalogue.

Revision ID: 003
Revises: 002
Create Date: 2024-12-17 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Drop old detection-era tables (if they exist) ──────────────────────
    for tbl in [
        "detection_results",
        "api_usage",
        "organization_blocks",
        "consent_records",
        "cookie_preferences",
        "age_verifications",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")

    # ── Alter existing users table to marketplace shape ─────────────────────
    # Add new columns (idempotent: ignore if already present)
    for col, type_, kwargs in [
        ("username",          sa.String(),  {"nullable": True}),
        ("role",              sa.String(),  {"nullable": True, "server_default": "artist"}),
        ("bio",               sa.Text(),    {"nullable": True}),
        ("avatar_url",        sa.String(),  {"nullable": True}),
        ("website",           sa.String(),  {"nullable": True}),
        ("location",          sa.String(),  {"nullable": True}),
        ("stripe_account_id", sa.String(),  {"nullable": True}),
        ("stripe_customer_id",sa.String(),  {"nullable": True}),
        ("stripe_onboarded",  sa.Boolean(), {"nullable": True, "server_default": "false"}),
        ("is_verified",       sa.Boolean(), {"nullable": True, "server_default": "false"}),
        ("consent_terms",     sa.Boolean(), {"nullable": True, "server_default": "false"}),
        ("consent_date",      sa.DateTime(),{"nullable": True}),
    ]:
        try:
            op.add_column("users", sa.Column(col, type_, **kwargs))
        except Exception:
            pass  # column already exists

    # ── artist_profiles ──────────────────────────────────────────────────────
    op.create_table(
        "artist_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("specialties", postgresql.JSON(), nullable=True, server_default="[]"),
        sa.Column("portfolio_url", sa.String(), nullable=True),
        sa.Column("social_links", postgresql.JSON(), nullable=True, server_default="{}"),
        sa.Column("verified_artist", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("total_sales", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_earnings", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
    )

    # ── company_profiles ────────────────────────────────────────────────────
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("company_size", sa.String(), nullable=True),
        sa.Column("use_case", sa.Text(), nullable=True),
        sa.Column("verified_company", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("total_purchases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_spent", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )

    # ── creative_works ───────────────────────────────────────────────────────
    op.create_table(
        "creative_works",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("work_type", sa.String(), nullable=False),   # image|audio|video|text|dataset
        sa.Column("file_format", sa.String(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("dimensions", sa.String(), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True, unique=True),
        sa.Column("feature_path", sa.String(), nullable=True),
        sa.Column("preview_url", sa.String(), nullable=True),
        sa.Column("tags", postgresql.JSON(), nullable=True, server_default="[]"),
        sa.Column("style", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="upload"),
        sa.Column("source_dataset", sa.String(), nullable=True),
        sa.Column("image_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("upload_proof_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── listings ─────────────────────────────────────────────────────────────
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_id", sa.Integer(), sa.ForeignKey("creative_works.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("artist_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("license_type", sa.String(), nullable=False),
        sa.Column("license_details", sa.Text(), nullable=True),
        sa.Column("max_buyers", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── purchases ────────────────────────────────────────────────────────────
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("platform_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("seller_payout", sa.Numeric(10, 2), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(), nullable=True, unique=True),
        sa.Column("stripe_transfer_id", sa.String(), nullable=True),
        sa.Column("stripe_charge_id", sa.String(), nullable=True),
        sa.Column("license_key", sa.String(32), nullable=True, unique=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("purchased_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("download_expires_at", sa.DateTime(), nullable=True),
    )

    # ── public_dataset_entries ───────────────────────────────────────────────
    op.create_table(
        "public_dataset_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url", sa.String(), nullable=False, unique=True),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("work_type", sa.String(), nullable=True),
        sa.Column("file_format", sa.String(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("dataset_source", sa.String(), nullable=True),
        sa.Column("crawl_id", sa.String(), nullable=True),
        sa.Column("license_detected", sa.String(), nullable=True),
        sa.Column("title_detected", sa.String(), nullable=True),
        sa.Column("author_detected", sa.String(), nullable=True),
        sa.Column("indexed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("discovered_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── indexes ───────────────────────────────────────────────────────────────
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_artist", "listings", ["artist_id"])
    op.create_index("ix_purchases_buyer", "purchases", ["buyer_id"])
    op.create_index("ix_creative_works_owner", "creative_works", ["owner_id"])
    op.create_index("ix_creative_works_type", "creative_works", ["work_type"])
    op.create_index("ix_public_dataset_source", "public_dataset_entries", ["dataset_source"])


def downgrade() -> None:
    for idx in [
        "ix_public_dataset_source",
        "ix_creative_works_type",
        "ix_creative_works_owner",
        "ix_purchases_buyer",
        "ix_listings_artist",
        "ix_listings_status",
    ]:
        op.drop_index(idx, if_exists=True)

    for tbl in [
        "public_dataset_entries",
        "purchases",
        "listings",
        "creative_works",
        "company_profiles",
        "artist_profiles",
    ]:
        op.drop_table(tbl, if_exists=True)
