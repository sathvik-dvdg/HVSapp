from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.modules.medication.models import OrderStatus, TaskStatus


class MedicationOrderBase(BaseModel):
    encounter_id: Optional[int] = None
    patient_id: Optional[str] = None
    drug_name: str
    dose: str
    route: str
    frequency: str
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    special_instructions: Optional[str] = None
    minimum_dose_interval_minutes: int = 60

    @model_validator(mode="after")
    def validate_target_reference(self) -> "MedicationOrderBase":
        if self.encounter_id is None and self.patient_id is None:
            raise ValueError("Either encounter_id or patient_id must be provided")
        return self

class MedicationOrderCreate(MedicationOrderBase):
    pass

class MedicationOrderRead(MedicationOrderBase):
    id: int
    ordered_by: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class MedicationTaskRead(BaseModel):
    id: int
    order_id: int
    encounter_id: int
    assigned_nurse_id: Optional[int] = None
    scheduled_at: datetime
    due_by: datetime
    status: str
    administered_at: Optional[datetime] = None
    administered_by: Optional[int] = None
    witness_id: Optional[int] = None
    skipped_reason: Optional[str] = None
    notes: Optional[str] = None
    last_escalation_level: Optional[int] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_date_of_birth: Optional[date] = None
    bed_number: Optional[str] = None
    drug_name: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MedicationTaskAdminister(BaseModel):
    patient_verified: bool = Field(default=False)
    drug_name_confirmed: bool = Field(default=False)
    witness_id: Optional[int] = None
    override_reason: Optional[str] = None
    supervisor_override_id: Optional[str] = None
    notes: Optional[str] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None
