# app/models/note.py
import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, DateTime, func, Enum as SQLEnum, ForeignKey, Text
)
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

# For type hints without circular imports
if TYPE_CHECKING:
    from .user import User  # noqa: F401
    from .encounter import Encounter  # noqa: F401


class NoteType(str, enum.Enum):
    """Enumeration for different types of clinical notes."""
    DOCTOR_DICTATION = "doctor_dictation"
    NURSE_UPDATE = "nurse_update"
    HANDOFF_SUMMARY = "handoff_summary"
    OTHER = "other"


class ClinicalNote(Base):
    """
    SQLAlchemy model representing a single clinical note associated with an encounter.
    This table stores the text from ASR dictation or manual entries.
    """
    __tablename__ = "clinical_notes"

    # --- Columns ---
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    note_type: Mapped[NoteType] = Column(
        SQLEnum(NoteType), index=True, nullable=False, default=NoteType.OTHER
    )
    content: Mapped[str] = Column(Text, nullable=False)  # The actual text

    # Timestamps
    created_at: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # updated_at is omitted, assuming notes are immutable once created

    # --- Foreign Keys ---
    encounter_id: Mapped[int] = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    author_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False, index=True) # User who wrote/dictated

    # --- Relationships ---
    # Many-to-one: Many Notes belong to one Encounter
    encounter: Mapped["Encounter"] = relationship("Encounter", back_populates="notes")

    # Many-to-one: Many Notes are authored by one User
    author: Mapped["User"] = relationship("User", back_populates="authored_notes")

    def __repr__(self) -> str:
        return f"<ClinicalNote(id={self.id}, encounter_id={self.encounter_id}, type='{self.note_type}')>"