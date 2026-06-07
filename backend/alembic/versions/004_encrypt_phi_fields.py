"""Encrypt PHI patient fields in place.

Revision ID: 004_encrypt_phi_fields
Revises: 002_create_clinical_tables
"""

from __future__ import annotations

import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine


revision = "004_encrypt_phi_fields"
down_revision = "002_create_clinical_tables"
branch_labels = None
depends_on = None

BATCH_SIZE = 100


def _get_phi_encryption_key() -> str:
    key = os.getenv("PHI_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("PHI_ENCRYPTION_KEY must be set before running migration 004_encrypt_phi_fields")
    return key


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        "patients",
        sa.Column(
            "phased_encryption_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("patients", "phone_number", existing_type=sa.String(length=20), type_=sa.Text(), existing_nullable=True)
    op.alter_column("patients", "emergency_contact", existing_type=sa.String(length=200), type_=sa.Text(), existing_nullable=True)
    op.execute(
        "ALTER TABLE patients ALTER COLUMN known_allergies TYPE TEXT USING "
        "CASE WHEN known_allergies IS NULL THEN NULL ELSE to_json(known_allergies)::text END"
    )
    op.execute(
        "ALTER TABLE patients ALTER COLUMN risk_flags TYPE TEXT USING "
        "CASE WHEN risk_flags IS NULL THEN NULL ELSE to_json(risk_flags)::text END"
    )

    key = _get_phi_encryption_key()
    metadata = sa.MetaData()
    raw_patients = sa.Table(
        "patients",
        metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("phone_number", sa.Text()),
        sa.Column("emergency_contact", sa.Text()),
        sa.Column("known_allergies", sa.Text()),
        sa.Column("risk_flags", sa.Text()),
        sa.Column("phased_encryption_complete", sa.Boolean()),
    )
    encrypted_patients = sa.Table(
        "patients",
        sa.MetaData(),
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("phone_number", EncryptedType(sa.Text(), key, AesGcmEngine, "pkcs5")),
        sa.Column("emergency_contact", EncryptedType(sa.Text(), key, AesGcmEngine, "pkcs5")),
        sa.Column("known_allergies", EncryptedType(sa.Text(), key, AesGcmEngine, "pkcs5")),
        sa.Column("risk_flags", EncryptedType(sa.Text(), key, AesGcmEngine, "pkcs5")),
        sa.Column("phased_encryption_complete", sa.Boolean()),
    )

    session = Session(bind=bind)
    try:
        while True:
            rows = session.execute(
                sa.select(
                    raw_patients.c.id,
                    raw_patients.c.phone_number,
                    raw_patients.c.emergency_contact,
                    raw_patients.c.known_allergies,
                    raw_patients.c.risk_flags,
                )
                .where(raw_patients.c.phased_encryption_complete.is_(False))
                .order_by(raw_patients.c.id.asc())
                .limit(BATCH_SIZE)
            ).mappings().all()

            if not rows:
                break

            for row in rows:
                update_values: dict[str, object] = {
                    "phased_encryption_complete": True,
                }
                for field_name in (
                    "phone_number",
                    "emergency_contact",
                    "known_allergies",
                    "risk_flags",
                ):
                    field_value = row[field_name]
                    if field_value is not None:
                        update_values[field_name] = field_value

                session.execute(
                    encrypted_patients.update()
                    .where(encrypted_patients.c.id == row["id"])
                    .values(**update_values)
                )

            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    op.alter_column(
        "patients",
        "phased_encryption_complete",
        server_default=None,
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )


def downgrade() -> None:
    raise RuntimeError("Migration 004_encrypt_phi_fields is irreversible.")
