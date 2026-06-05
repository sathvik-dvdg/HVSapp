# app/modules/medication/models.py
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text, func
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
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=False)
    route = Column(String(100))
    frequency = Column(String(100), nullable=False) # e.g., "q8h", "BID"
    
    start_date = Column(DateTime, default=func.now(), nullable=False)
    end_date = Column(DateTime)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    tasks = relationship("MedicationTask", back_populates="order", cascade="all, delete-orphan")

class MedicationTask(Base):
    """SQLAlchemy model for individual scheduled administrations."""
    __tablename__ = "medication_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("medication_orders.id"), nullable=False)
    assigned_nurse_id = Column(Integer, ForeignKey("users.id"))
    
    scheduled_time = Column(DateTime, nullable=False, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    administered_time = Column(DateTime)
    notes = Column(Text)

    # Relationships
    order = relationship("MedicationOrder", back_populates="tasks")
