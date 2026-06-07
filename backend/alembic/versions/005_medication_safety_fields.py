"""Add medication safety fields.

Revision ID: 005_medication_safety_fields
Revises: 004_encrypt_phi_fields
"""

from alembic import op
import sqlalchemy as sa


revision = "005_medication_safety_fields"
down_revision = "004_encrypt_phi_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "medication_orders",
        sa.Column(
            "minimum_dose_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
    )
    op.add_column(
        "medication_tasks",
        sa.Column("last_escalation_level", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("medication_tasks", "last_escalation_level")
    op.drop_column("medication_orders", "minimum_dose_interval_minutes")
