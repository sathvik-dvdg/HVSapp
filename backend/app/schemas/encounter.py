# app/schemas/encounter.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Import Enums defined in the model
from app.models.encounter import EncounterType, EncounterStatus, LabReportStatus

# --- Base Schema ---
class EncounterBase(BaseModel):
    patient_id: str
    encounter_type: EncounterType
    # Add other fields potentially captured at triage/admission if needed

# --- Schema for Creating an Encounter (during Triage) ---
class EncounterCreate(EncounterBase):
    current_status: EncounterStatus = EncounterStatus.PENDING_TRIAGE

# --- Schema for Updating Encounter (e.g., admitting, discharging) ---
class EncounterUpdate(BaseModel):
    encounter_type: Optional[EncounterType] = None
    current_status: Optional[EncounterStatus] = None
    admitted_at: Optional[datetime] = None
    discharged_at: Optional[datetime] = None
    medication_schedule_notes: Optional[str] = None
    next_med_due_at: Optional[datetime] = None
    lab_report_status: Optional[LabReportStatus] = None
    lab_report_expected_at: Optional[datetime] = None
    estimated_length_of_stay: Optional[str] = None

# --- Schema for Reading Encounter Data ---
class EncounterRead(EncounterBase):
    id: int
    current_status: EncounterStatus
    admitted_at: Optional[datetime] = None
    discharged_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    medication_schedule_notes: Optional[str] = None
    next_med_due_at: Optional[datetime] = None
    lab_report_status: LabReportStatus
    lab_report_expected_at: Optional[datetime] = None
    estimated_length_of_stay: Optional[str] = None

    class Config:
        from_attributes = True  # Enable ORM mode (SQLAlchemy -> Pydantic)

# --- Schema for Lab Status Update Endpoint ---
class LabStatusUpdate(BaseModel):
    new_status: LabReportStatus
    expected_at: Optional[datetime] = None

# --- Schema for Critical Alerts Endpoint ---
class CriticalAlerts(BaseModel):
    """Schema to unify all critical alerts for the Dashboard."""
    medication_overdue: List[EncounterRead]
    lab_reports_delayed: List[EncounterRead]

    class Config:
        from_attributes = True