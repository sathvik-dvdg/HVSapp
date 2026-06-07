import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, Column, Date, DateTime, String, Text, func
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from src.db.base_class import Base
from src.config.settings import settings

# This helps type checkers understand the relationship without circular imports
if TYPE_CHECKING:
    from .encounter import Encounter  # noqa: F401


class Patient(Base):
    """
    SQLAlchemy model representing a patient registered in the system.
    """
    __tablename__ = "patients"

    # --- Columns ---
    # We use String for the ID to store our custom format (e.g., YYYYMMDD-XXXX)
    id: Mapped[str] = Column(String, primary_key=True, index=True)
    full_name: Mapped[str] = Column(String, index=True, nullable=False)
    date_of_birth: Mapped[datetime.date | None] = Column(Date, nullable=True)
    contact_info: Mapped[str | None] = Column(String, nullable=True)
    gender: Mapped[str | None] = Column(String(20), nullable=True)
    blood_group: Mapped[str | None] = Column(String(10), nullable=True)
    # Array-backed clinical values are stored as encrypted JSON strings.
    phone_number: Mapped[str | None] = Column(
        EncryptedType(Text, settings.PHI_ENCRYPTION_KEY, AesGcmEngine, "pkcs5"),
        nullable=True,
    )
    emergency_contact: Mapped[str | None] = Column(
        EncryptedType(Text, settings.PHI_ENCRYPTION_KEY, AesGcmEngine, "pkcs5"),
        nullable=True,
    )
    known_allergies: Mapped[str | None] = Column(
        EncryptedType(Text, settings.PHI_ENCRYPTION_KEY, AesGcmEngine, "pkcs5"),
        nullable=True,
    )
    risk_flags: Mapped[str | None] = Column(
        EncryptedType(Text, settings.PHI_ENCRYPTION_KEY, AesGcmEngine, "pkcs5"),
        nullable=True,
    )
    ward: Mapped[str | None] = Column(String(100), nullable=True)
    bed_number: Mapped[str | None] = Column(String(20), nullable=True)
    phased_encryption_complete: Mapped[bool] = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Timestamps
    registration_timestamp: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime | None] = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # --- Relationships ---
    # One-to-Many: One Patient can have many Encounters
    encounters: Mapped[List["Encounter"]] = relationship(
        "Encounter",
        back_populates="patient", # Links to the 'patient' attribute in the Encounter model
        cascade="all, delete-orphan", # Deletes encounters if the patient is deleted
        lazy="selectin" # Eagerly load encounters via a separate SELECT IN query
    )

    def __repr__(self) -> str:
        return f"<Patient(id='{self.id}', name='{self.full_name}')>"
