"""Extend users, patients, encounters with clinical fields

Revision ID: 001_clinical_extensions
Revises: 73dad259939a
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ── users ──────────────────────────────────────────────────────────────
    op.add_column('users', sa.Column('refresh_token', sa.String(512), nullable=True))
    op.add_column('users', sa.Column('device_token', sa.String(512), nullable=True))
    op.add_column('users', sa.Column('last_active', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true'))
    op.add_column('users', sa.Column('ward_assignment', sa.String(100), nullable=True))

    # Add new roles to existing ENUM (PostgreSQL-specific, non-transactional)
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'RECEPTIONIST'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'LAB_TECHNICIAN'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PHARMACIST'")

    # ── patients ───────────────────────────────────────────────────────────
    op.add_column('patients', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('patients', sa.Column('gender', sa.String(20), nullable=True))
    op.add_column('patients', sa.Column('blood_group', sa.String(10), nullable=True))
    op.add_column('patients', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('patients', sa.Column('emergency_contact', sa.String(200), nullable=True))
    op.add_column('patients', sa.Column('known_allergies',
        postgresql.ARRAY(sa.Text()), server_default='{}'))
    op.add_column('patients', sa.Column('risk_flags',
        postgresql.ARRAY(sa.Text()), server_default='{}'))
    op.add_column('patients', sa.Column('ward', sa.String(100), nullable=True))
    op.add_column('patients', sa.Column('bed_number', sa.String(20), nullable=True))
    op.add_column('patients', sa.Column('created_at',
        sa.DateTime(), server_default=sa.func.now()))

    # ── encounters ─────────────────────────────────────────────────────────
    op.add_column('encounters', sa.Column('handoff_status',
        sa.String(50), server_default='NOT_REQUIRED'))
    op.add_column('encounters', sa.Column('attending_nurse_id',
        sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('encounters', sa.Column('icu_flag',
        sa.Boolean(), server_default='false'))
    op.add_column('encounters', sa.Column('fall_risk_score', sa.Integer(), nullable=True))
    op.add_column('encounters', sa.Column('pain_score', sa.Integer(), nullable=True))
    op.add_column('encounters', sa.Column('last_vitals_at', sa.DateTime(), nullable=True))
    op.add_column('encounters', sa.Column('estimated_discharge', sa.Date(), nullable=True))
    op.add_column('encounters', sa.Column('updated_at', sa.DateTime(), nullable=True))

def downgrade():
    # Remove columns in reverse order
    for col in ['updated_at', 'estimated_discharge', 'last_vitals_at',
                'pain_score', 'fall_risk_score', 'icu_flag',
                'attending_nurse_id', 'handoff_status']:
        op.drop_column('encounters', col)

    for col in ['created_at', 'bed_number', 'ward', 'risk_flags',
                'known_allergies', 'emergency_contact', 'phone_number',
                'blood_group', 'gender', 'date_of_birth']:
        op.drop_column('patients', col)

    for col in ['ward_assignment', 'is_active', 'last_active',
                'device_token', 'refresh_token']:
        op.drop_column('users', col)
    # Note: cannot remove ENUM values in PostgreSQL without full type recreation