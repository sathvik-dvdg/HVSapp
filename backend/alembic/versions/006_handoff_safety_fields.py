"""Add handoff safety fields when handoff tables exist.

Revision ID: 006_handoff_safety_fields
Revises: 005_medication_safety_fields
"""

from alembic import op
import sqlalchemy as sa


revision = "006_handoff_safety_fields"
down_revision = "005_medication_safety_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "handoff_sessions" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("handoff_sessions")}
    if "last_escalation_level" not in column_names:
        op.add_column("handoff_sessions", sa.Column("last_escalation_level", sa.Integer(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "handoff_sessions" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("handoff_sessions")}
    if "last_escalation_level" in column_names:
        op.drop_column("handoff_sessions", "last_escalation_level")
