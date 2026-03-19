# app/api/endpoints/patients.py
import logging
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

# Import project components
from app.api import deps # Contains get_current_user dependency
from app.db.session import get_db
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientRead
from app.services import patient_service # Import the patient service

log = logging.getLogger(__name__)

# --- API Router Initialization ---
router = APIRouter()
# ---------------------------------

# --- ENDPOINT 1: REGISTER NEW PATIENT ---
@router.post(
    "/register",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(deps.get_current_user)], # Requires authentication
    summary="Register New Patient",
    description="Creates a new patient record in the system."
)
def register_new_patient(
    *,
    db: Session = Depends(get_db),
    patient_in: PatientCreate,
) -> Any:
    """
    Register a new patient. Requires authentication.
    """
    log.info(f"Received request to register patient: {patient_in.full_name}")
    patient = patient_service.create_patient(db=db, patient_in=patient_in)
    
    if patient is None:
        log.error(f"Failed to register patient: {patient_in.full_name}. Service returned None.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not register patient due to an internal error (e.g., ID collision).",
        )
    
    log.info(f"Successfully registered patient ID: {patient.id}")
    return patient

# --- ENDPOINT 2: GET PATIENT DETAILS BY ID ---
@router.get(
    "/{patient_id}",
    response_model=PatientRead,
    dependencies=[Depends(deps.get_current_user)], # Requires authentication
    summary="Get Patient Details",
    description="Retrieve details for a specific patient by their unique ID."
)
def get_patient_details(
    *,
    db: Session = Depends(get_db),
    patient_id: str, # Get ID from the path parameter
) -> Any:
    """
    Retrieve details for a specific patient by their ID.
    """
    log.info(f"Request received to fetch patient details for ID: {patient_id}")
    patient = patient_service.get_patient_by_id(db=db, patient_id=patient_id)
    
    if patient is None:
        log.warning(f"Patient with ID '{patient_id}' not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    log.info(f"Returning details for patient ID: {patient.id}")
    return patient

# --- ENDPOINT 3: SEARCH FOR PATIENTS BY NAME ---
@router.get(
    "/search/", # Note the trailing slash: /api/v1/patients/search/?query=...
    response_model=List[PatientRead],
    dependencies=[Depends(deps.get_current_user)], # Requires authentication
    summary="Search Patients by Name",
    description="Search for patients by name (case-insensitive partial match). Includes pagination."
)
def search_for_patients(
    *,
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=1, description="Partial name to search for"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records to return (max 200)"),
) -> Any:
    """
    Search for patients by name with pagination.
    """
    log.info(f"Received patient search request with query: '{query}'")
    patients = patient_service.search_patients_by_name(
        db=db, name_query=query, skip=skip, limit=limit
    )
    log.info(f"Returning {len(patients)} patients for search query: '{query}'")
    return patients

# --- ENDPOINT 4: GET PATIENT HISTORY TIMELINE ---
@router.get(
    "/{patient_id}/history",
    response_model=List[Dict[str, Any]], # Returns a list of generic dictionaries
    dependencies=[Depends(deps.get_current_user)],
    summary="Get Full Patient History Timeline",
    description="Retrieves a chronological timeline of all encounters, notes, and tasks for a patient."
)
def get_patient_history_endpoint(
    *,
    db: Session = Depends(get_db),
    patient_id: str,
) -> List[Dict[str, Any]]:
    """
    Retrieves the comprehensive history for a given patient ID. Requires authentication.
    """
    log.info(f"Request received for history of patient ID: {patient_id}")
    # First, check if the patient exists
    patient = patient_service.get_patient_by_id(db=db, patient_id=patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Call the service function to generate the unified history timeline
    history = patient_service.get_patient_history(db=db, patient_id=patient_id)
    log.info(f"Returning {len(history)} history items for patient ID: {patient_id}")
    return history