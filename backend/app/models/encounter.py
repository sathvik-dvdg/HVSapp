# app/models/encounter.py
import datetime
import enum
from typing import List, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, DateTime, func, Enum as SQLEnum, ForeignKey, Text
)
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

# This helps type checkers understand relationships without circular imports
if TYPE_CHECKING:
    from .patient import Patient  # noqa: F401
    from .note import ClinicalNote  # noqa: F401
    from .task import NurseTask  # noqa: F401


# --- Enums for structured data ---

class EncounterType(str, enum.Enum):
    TRIAGE = "triage"
    ADMISSION = "admission"
    OUTPATIENT = "outpatient"


class EncounterStatus(str, enum.Enum):
    ACTIVE = "active"
    DISCHARGED = "discharged"
    PENDING_TRIAGE = "pending_triage"


class LabReportStatus(str, enum.Enum):
    NOT_ORDERED = "not_ordered"
    ORDERED = "ordered"
    PENDING = "pending"
    RECEIVED = "received"
    DELAYED = "delayed"


class Encounter(Base):
    """
    SQLAlchemy model representing a single patient encounter (visit/admission).
    This table links patients to their notes and tasks for a specific visit.
    """
    __tablename__ = "encounters"

    # --- Columns ---
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    
    encounter_type: Mapped[EncounterType] = Column(
        SQLEnum(EncounterType), index=True, nullable=False
    )
    current_status: Mapped[EncounterStatus] = Column(
        SQLEnum(EncounterStatus), index=True, nullable=False, default=EncounterStatus.PENDING_TRIAGE
    )
    
    # New field requested by frontend
    estimated_length_of_stay: Mapped[str | None] = Column(String, nullable=True) # e.g., "3 days"

    # Timestamps
    admitted_at: Mapped[datetime.datetime | None] = Column(DateTime(timezone=True), nullable=True)
    discharged_at: Mapped[datetime.datetime | None] = Column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime | None] = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Simplified Tracking Fields (for Phase 5)
    medication_schedule_notes: Mapped[str | None] = Column(Text, nullable=True)
    next_med_due_at: Mapped[datetime.datetime | None] = Column(DateTime(timezone=True), nullable=True)
    lab_report_status: Mapped[LabReportStatus] = Column(
        SQLEnum(LabReportStatus), nullable=False, default=LabReportStatus.NOT_ORDERED
    )
    lab_report_expected_at: Mapped[datetime.datetime | None] = Column(DateTime(timezone=True), nullable=True)

    # --- Foreign Keys ---
    patient_id: Mapped[str] = Column(String, ForeignKey("patients.id"), nullable=False, index=True)

    # --- Relationships ---
    # Many-to-one: Many Encounters belong to one Patient
    patient: Mapped["Patient"] = relationship("Patient", back_populates="encounters")

    # One-to-many: One Encounter can have many Clinical Notes
    notes: Mapped[List["ClinicalNote"]] = relationship(
        "ClinicalNote", back_populates="encounter", cascade="all, delete-orphan", lazy="selectin"
    )

    # One-to-many: One Encounter can have many Nurse Tasks
    tasks: Mapped[List["NurseTask"]] = relationship(
        "NurseTask", back_populates="encounter", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Encounter(id={self.id}, patient_id='{self.patient_id}', type='{self.encounter_type}')>"