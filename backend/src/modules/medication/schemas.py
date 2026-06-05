# app/modules/medication/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.modules.medication.models import OrderStatus, TaskStatus

class MedicationOrderBase(BaseModel):
    patient_id: int
    medication_name: str
    dosage: str
    route: Optional[str] = None
    frequency: str
    end_date: Optional[datetime] = None

class MedicationOrderCreate(MedicationOrderBase):
    pass

class MedicationOrderRead(MedicationOrderBase):
    id: int
    doctor_id: int
    start_date: datetime
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

# --- Medication Task Schemas ---
class MedicationTaskRead(BaseModel):
    id: int
    order_id: int
    assigned_nurse_id: Optional[int] = None
    scheduled_time: datetime
    status: TaskStatus
    administered_time: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None
