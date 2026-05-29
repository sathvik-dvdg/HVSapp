import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import relationship, Mapped
from src.db.base_class import Base

class NoteType(str, enum.Enum):
    DOCTOR_DICTATION = "DOCTOR_DICTATION"
    NURSE_UPDATE = "NURSE_UPDATE"
    HANDOFF_SUMMARY = "HANDOFF_SUMMARY"
    OTHER = "OTHER"

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    note_type: Mapped[NoteType] = Column(SQLEnum(NoteType), nullable=False)
    content: Mapped[str] = Column(Text, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    encounter_id: Mapped[int] = Column(Integer, ForeignKey("encounters.id"))
    author_id: Mapped[int] = Column(Integer, ForeignKey("users.id"))
    
    encounter = relationship("Encounter", back_populates="notes")
    author = relationship("User", back_populates="authored_notes")