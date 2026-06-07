import enum
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship
from src.db.base_class import Base


class OrderStatus(str, enum.Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    ADMINISTERED = "administered"
    SKIPPED = "skipped"
    MISSED = "missed"

class MedicationOrder(Base):
    """SQLAlchemy model for a Doctor's medication order/prescription."""
    __tablename__ = "medication_orders"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    ordered_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    drug_name = Column(String(200), nullable=False)
    dose = Column(String(100), nullable=False)
    route = Column(String(100))
    frequency = Column(String(100), nullable=False)
    start_datetime = Column(DateTime, default=func.now(), nullable=False)
    end_datetime = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    special_instructions = Column(Text)
    minimum_dose_interval_minutes = Column(Integer, nullable=False, default=60, server_default="60")
    created_at = Column(DateTime, default=func.now())

    tasks = relationship("MedicationTask", back_populates="order", cascade="all, delete-orphan")


class MedicationTask(Base):
    """SQLAlchemy model for individual scheduled administrations."""
    __tablename__ = "medication_tasks"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("medication_orders.id"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    assigned_nurse_id = Column(Integer, ForeignKey("users.id"))

    scheduled_at = Column(DateTime, nullable=False, index=True)
    due_by = Column(DateTime, nullable=False)
    status = Column(String(50), default=TaskStatus.PENDING.value, nullable=False)
    administered_at = Column(DateTime)
    administered_by = Column(Integer, ForeignKey("users.id"))
    witness_id = Column(Integer, ForeignKey("users.id"))
    skipped_reason = Column(Text)
    notes = Column(Text)
    escalation_level = Column(Integer, nullable=False, default=0, server_default="0")
    last_escalation_level = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    order = relationship("MedicationOrder", back_populates="tasks")
