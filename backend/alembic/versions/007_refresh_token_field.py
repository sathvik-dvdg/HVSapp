"""Add hashed refresh token field.

Revision ID: 007_refresh_token_field
Revises: 006_handoff_safety_fields
"""

from alembic import op
import sqlalchemy as sa


revision = "007_refresh_token_field"
down_revision = "006_handoff_safety_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_refresh_token", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "hashed_refresh_token")
