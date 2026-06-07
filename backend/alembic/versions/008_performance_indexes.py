"""Add performance indexes.

Revision ID: 008_performance_indexes
Revises: 007_refresh_token_field
"""

from alembic import op
import sqlalchemy as sa


revision = "008_performance_indexes"
down_revision = "007_refresh_token_field"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if 'vitals' in tables:
        op.create_index('ix_vitals_encounter_id', 'vitals', ['encounter_id'])
        op.create_index('ix_vitals_recorded_at_desc', 'vitals', ['recorded_at'], postgresql_using='btree')
    if 'medication_tasks' in tables:
        op.create_index('ix_medication_tasks_composite', 'medication_tasks', ['status', 'scheduled_at'])
    if 'handoff_sessions' in tables:
        op.create_index('ix_handoff_sessions_encounter_id', 'handoff_sessions', ['encounter_id'])
    if 'audit_logs' in tables:
        op.create_index('ix_audit_logs_entity', 'audit_logs', ['resource_type', 'resource_id'])
    if 'notifications' in tables:
        op.create_index('ix_notifications_recipient_read', 'notifications', ['recipient_id', 'is_read'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if 'notifications' in tables:
        op.drop_index('ix_notifications_recipient_read', table_name='notifications')
    if 'audit_logs' in tables:
        op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    if 'handoff_sessions' in tables:
        op.drop_index('ix_handoff_sessions_encounter_id', table_name='handoff_sessions')
    if 'medication_tasks' in tables:
        op.drop_index('ix_medication_tasks_composite', table_name='medication_tasks')
    if 'vitals' in tables:
        op.drop_index('ix_vitals_recorded_at_desc', table_name='vitals')
        op.drop_index('ix_vitals_encounter_id', table_name='vitals')
