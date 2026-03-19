# app/models/user.py
import datetime
import enum
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

# This helps type checkers understand relationships without circular imports
if TYPE_CHECKING:
    from .note import ClinicalNote  # noqa: F401
    from .task import NurseTask  # noqa: F401


class UserRole(str, enum.Enum):
    """Enumeration for user roles within the system."""
    DOCTOR = "doctor"
    NURSE = "nurse"
    ADMIN = "admin"


class User(Base):
    """
    SQLAlchemy model representing a user (Doctor, Nurse, Admin) of the application.
    """
    __tablename__ = "users"

    # --- Columns ---
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    username: Mapped[str] = Column(String, unique=True, index=True, nullable=False)  # Use email
    hashed_password: Mapped[str] = Column(String, nullable=False)
    full_name: Mapped[str | None] = Column(String, index=True, nullable=True)
    role: Mapped[UserRole] = Column(SQLEnum(UserRole), nullable=False, index=True)

    # Timestamps (managed by the database)
    created_at: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime | None] = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # --- Relationships ---
    # One-to-many: One User can author many Clinical Notes.
    authored_notes: Mapped[List["ClinicalNote"]] = relationship(
        "ClinicalNote",
        back_populates="author",  # Links to 'author' in ClinicalNote
        lazy="selectin"
    )

    # One-to-many: One User (Nurse) can be assigned many Tasks
    assigned_tasks: Mapped[List["NurseTask"]] = relationship(
        "NurseTask",
        back_populates="assigned_nurse",  # Links to 'assigned_nurse' in NurseTask
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"