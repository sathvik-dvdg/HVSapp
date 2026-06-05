# app/modules/medication/router.py
import logging
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.api.dependencies import get_current_user
from src.modules.auth.models import User, UserRole
from src.modules.medication import schemas, service

log = logging.getLogger(__name__)
router = APIRouter()

# --- Order Endpoints ---
@router.post("/orders", response_model=schemas.MedicationOrderRead, status_code=status.HTTP_201_CREATED)
def create_medication_order(
    order_in: schemas.MedicationOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can prescribe medication")
    return service.create_order(db=db, order_in=order_in, doctor_id=current_user.id)

@router.get("/orders/{patient_id}", response_model=List[schemas.MedicationOrderRead])
def get_patient_orders(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    return service.get_orders_by_patient(db=db, patient_id=patient_id)

@router.put("/orders/{order_id}/status", response_model=schemas.MedicationOrderRead)
def update_order_status(order_id: int, status_update: schemas.OrderStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can update order status")
    order = service.update_order_status(db=db, order_id=order_id, status=status_update.status)
    if not order: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

# --- Task Endpoints ---
@router.get("/tasks/{patient_id}", response_model=List[schemas.MedicationTaskRead])
def get_patient_tasks(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    """Fetch all scheduled medication tasks for a patient."""
    return service.get_tasks_for_patient(db=db, patient_id=patient_id)

@router.put("/tasks/{task_id}/status", response_model=schemas.MedicationTaskRead)
def update_task_status(task_id: int, update_data: schemas.TaskStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    """Administer or skip a medication task. Restricted to Nurses."""
    if current_user.role not in (UserRole.NURSE, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only nurses can administer medication")
        
    task = service.update_task_status(db=db, task_id=task_id, nurse_id=current_user.id, status=update_data.status, notes=update_data.notes)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
