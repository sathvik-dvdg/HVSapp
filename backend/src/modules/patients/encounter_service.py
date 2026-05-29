# app/services/encounter_service.py
import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import project components
from src.modules.patients.encounter_models import Encounter, EncounterStatus, EncounterType, LabReportStatus
from src.modules.patients.encounter_schemas import EncounterCreate, EncounterUpdate

# Note: If 'Patient' here is your SQLAlchemy DB model, use .models. 
# If it is a Pydantic schema, use .schemas.
from src.modules.patients.models import Patient

log = logging.getLogger(__name__)

# --- Encounter CRUD Functions ---

def get_encounter_by_id(db: Session, *, encounter_id: int) -> Optional[Encounter]:
    """Fetches a single encounter by its ID."""
    log.debug(f"Querying for encounter with ID: {encounter_id}")
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        log.warning(f"Encounter not found for ID: {encounter_id}")
    return encounter

def create_initial_encounter(db: Session, *, encounter_in: EncounterCreate) -> Optional[Encounter]:
    """
    Creates a new encounter, typically during patient triage or registration.
    Validates that the patient exists.
    """
    log.info(f"Attempting to create initial encounter for patient ID: {encounter_in.patient_id}")

    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == encounter_in.patient_id).first()
    if not patient:
        log.error(f"Cannot create encounter: Patient with ID '{encounter_in.patient_id}' not found.")
        return None

    try:
        db_encounter = Encounter(
            patient_id=encounter_in.patient_id,
            encounter_type=encounter_in.encounter_type,
            current_status=encounter_in.current_status or EncounterStatus.PENDING_TRIAGE,
        )
        db.add(db_encounter)
        db.commit()
        db.refresh(db_encounter)
        log.info(f"Successfully created encounter ID: {db_encounter.id} for patient ID: {db_encounter.patient_id}")
        return db_encounter
    except SQLAlchemyError as e:
        log.error(f"Database error during encounter creation: {e}", exc_info=True)
        db.rollback()
        return None
    except Exception as e:
        log.error(f"Unexpected error during encounter creation: {e}", exc_info=True)
        db.rollback()
        return None

def update_encounter(db: Session, *, encounter_id: int, encounter_update: EncounterUpdate) -> Optional[Encounter]:
    """
    Updates an existing encounter (e.g., admit, discharge, update status/notes).
    """
    log.info(f"Attempting to update encounter ID: {encounter_id}")
    db_encounter = get_encounter_by_id(db, encounter_id=encounter_id)
    if not db_encounter:
        return None # Encounter not found

    # Get only the fields that were actually passed in the request
    update_data = encounter_update.model_dump(exclude_unset=True)

    # --- Business Logic for Status Changes ---
    if "current_status" in update_data:
        new_status = update_data["current_status"]
        # Set timestamp if moving to 'ACTIVE' and it's not already set
        if new_status == EncounterStatus.ACTIVE and not db_encounter.admitted_at:
            update_data["admitted_at"] = datetime.now(timezone.utc)
            log.info(f"Setting admitted_at timestamp for encounter {encounter_id}")
        # Set timestamp if moving to 'DISCHARGED' and it's not already set
        elif new_status == EncounterStatus.DISCHARGED and not db_encounter.discharged_at:
            update_data["discharged_at"] = datetime.now(timezone.utc)
            log.info(f"Setting discharged_at timestamp for encounter {encounter_id}")

    try:
        # Apply all updates from the request
        for field, value in update_data.items():
            setattr(db_encounter, field, value)

        db.add(db_encounter)
        db.commit()
        db.refresh(db_encounter)
        log.info(f"Successfully updated encounter ID: {db_encounter.id}")
        return db_encounter
    except SQLAlchemyError as e:
        log.error(f"Database error during encounter update for ID {encounter_id}: {e}", exc_info=True)
        db.rollback()
        return None

def update_lab_status(
    db: Session,
    *,
    encounter_id: int,
    new_status: LabReportStatus,
    expected_at: Optional[datetime] = None
) -> Optional[Encounter]:
    """
    Updates the lab report status and expected delivery time for an encounter.
    """
    log.info(f"Attempting to update lab status for encounter ID {encounter_id} to {new_status}")
    db_encounter = get_encounter_by_id(db, encounter_id=encounter_id)
    if not db_encounter:
        log.warning(f"Lab status update failed: Encounter {encounter_id} not found.")
        return None
    try:
        db_encounter.lab_report_status = new_status
        db_encounter.lab_report_expected_at = expected_at
        if new_status == LabReportStatus.DELAYED:
            log.warning(f"Lab report for Encounter {encounter_id} marked as DELAYED!")
            # Future: Trigger real-time notification
        db.add(db_encounter)
        db.commit()
        db.refresh(db_encounter)
        log.info(f"Successfully updated lab status for encounter {encounter_id}.")
        return db_encounter
    except SQLAlchemyError as e:
        log.error(f"Database error during lab status update for ID {encounter_id}: {e}", exc_info=True)
        db.rollback()
        return None

# --- Alert Logic Functions ---

def get_medication_alerts(db: Session) -> List[Encounter]:
    """
    Retrieves all active encounters where the next medication is past due.
    """
    log.info("Querying for overdue medication alerts.")
    now_utc = datetime.now(timezone.utc)
    alerts = (
        db.query(Encounter)
        .filter(Encounter.current_status == EncounterStatus.ACTIVE)
        .filter(Encounter.next_med_due_at.is_not(None))
        .filter(Encounter.next_med_due_at < now_utc) # Due time is in the past
        .all()
    )
    log.info(f"Found {len(alerts)} medication alerts/overdue meds.")
    return alerts

def get_delayed_lab_alerts(db: Session) -> List[Encounter]:
    """
    Retrieves all active encounters flagged with DELAYED lab status.
    """
    log.info("Querying for delayed lab report alerts.")
    alerts = (
        db.query(Encounter)
        .filter(Encounter.current_status == EncounterStatus.ACTIVE)
        .filter(Encounter.lab_report_status == LabReportStatus.DELAYED)
        .all()
    )
    log.info(f"Found {len(alerts)} delayed lab report alerts.")
    return alerts