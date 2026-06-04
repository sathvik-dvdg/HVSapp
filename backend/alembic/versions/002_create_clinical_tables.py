"""Create vitals, medication_orders, medication_tasks, notifications, audit_logs"""

# revision identifiers, used by Alembic.
revision = '002_create_clinical_tables'
down_revision = '001_clinical_extensions'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    # ── vitals ─────────────────────────────────────────────────────────────
    op.create_table('vitals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id', name='fk_vitals_encounter'), nullable=False),
        sa.Column('recorded_by', sa.Integer(), sa.ForeignKey('users.id', name='fk_vitals_user'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('systolic_bp', sa.Integer()),
        sa.Column('diastolic_bp', sa.Integer()),
        sa.Column('heart_rate', sa.Integer()),
        sa.Column('spo2_percent', sa.Float()),
        sa.Column('temperature_c', sa.Float()),
        sa.Column('respiratory_rate', sa.Integer()),
        sa.Column('blood_glucose', sa.Float()),
        sa.Column('pain_score', sa.Integer()),
        sa.Column('gcs_score', sa.Integer()),
        sa.Column('notes', sa.Text()),
        sa.CheckConstraint('systolic_bp > 0', name='ck_vitals_systolic'),
        sa.CheckConstraint('gcs_score BETWEEN 3 AND 15', name='ck_vitals_gcs')
    )
    op.create_index('idx_vitals_encounter', 'vitals', ['encounter_id'])
    op.create_index('idx_vitals_recorded_at', 'vitals', ['recorded_at'])

    # ── medication_orders ──────────────────────────────────────────────────
    op.create_table('medication_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id', name='fk_med_orders_encounter'), nullable=False),
        sa.Column('ordered_by', sa.Integer(), sa.ForeignKey('users.id', name='fk_med_orders_user'), nullable=False),
        sa.Column('drug_name', sa.String(200), nullable=False),
        sa.Column('dose', sa.String(100), nullable=False),
        sa.Column('route', sa.String(50), nullable=False),
        sa.Column('frequency', sa.String(100), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('special_instructions', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_med_orders_encounter', 'medication_orders', ['encounter_id'])

    # ── medication_tasks ───────────────────────────────────────────────────
    op.create_table('medication_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('medication_orders.id', name='fk_med_tasks_order'), nullable=False),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id', name='fk_med_tasks_encounter'), nullable=False),
        sa.Column('assigned_nurse_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_med_tasks_nurse')),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('due_by', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('administered_at', sa.DateTime()),
        sa.Column('administered_by', sa.Integer(), sa.ForeignKey('users.id', name='fk_med_tasks_admin_user')),
        sa.Column('witness_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_med_tasks_witness')),
        sa.Column('skipped_reason', sa.Text()),
        sa.Column('notes', sa.Text()),
        sa.Column('escalation_level', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_med_tasks_scheduled', 'medication_tasks', ['scheduled_at'])
    op.create_index('idx_med_tasks_status', 'medication_tasks', ['status'])
    op.create_index('idx_med_tasks_encounter', 'medication_tasks', ['encounter_id'])

    # ── notifications ──────────────────────────────────────────────────────
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipient_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_notifications_recipient'), nullable=False),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_notifications_sender')),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('priority', sa.String(20), server_default='MEDIUM', nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('related_entity_type', sa.String(50)),
        sa.Column('related_entity_id', sa.Integer()),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('is_delivered', sa.Boolean(), server_default='false'),
        sa.Column('push_sent_at', sa.DateTime()),
        sa.Column('read_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_notifications_recipient', 'notifications', ['recipient_id', 'is_read'])

    # ── audit_logs ─────────────────────────────────────────────────────────
    op.create_table('audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_audit_user')),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(200)),
        sa.Column('patient_id', sa.String(100)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('request_payload', sa.JSON()),
        sa.Column('response_status', sa.Integer()),
        sa.Column('old_value', sa.JSON()),
        sa.Column('new_value', sa.JSON()),
        sa.Column('session_id', sa.String(200)),
        sa.Column('hash_chain', sa.String(256)),
    )
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_patient', 'audit_logs', ['patient_id'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])

def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('medication_tasks')
    op.drop_table('medication_orders')
    op.drop_table('vitals')