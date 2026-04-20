"""Add missing user columns

Revision ID: 004
Revises: 003
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to users table (idempotent)
    for col, type_, kwargs in [
        ("is_verified", sa.Boolean(), {"nullable": True, "server_default": "false"}),
        ("consent_terms", sa.Boolean(), {"nullable": True, "server_default": "false"}),
        ("consent_date", sa.DateTime(), {"nullable": True}),
    ]:
        try:
            op.add_column("users", sa.Column(col, type_, **kwargs))
        except Exception:
            pass  # column already exists


def downgrade() -> None:
    # Remove columns if needed
    for col in ["consent_date", "consent_terms", "is_verified"]:
        try:
            op.drop_column("users", col)
        except Exception:
            pass
