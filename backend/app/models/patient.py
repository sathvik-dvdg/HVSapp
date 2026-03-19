# app/models/patient.py
import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, String, Date, DateTime, func
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

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