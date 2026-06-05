# app/modules/medication/service.py
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from src.modules.medication.models import MedicationOrder, MedicationTask, OrderStatus, TaskStatus
from src.modules.medication.schemas import MedicationOrderCreate

log = logging.getLogger(__name__)

def parse_frequency_hours(frequency: str) -> int:
    """Parses standard medical frequency strings into hour intervals."""
    freq = frequency.lower().strip()
    if freq in ("daily", "qd"): return 24
    if freq == "bid": return 12
    if freq == "tid": return 8
    if freq == "qid": return 6
    
    match = re.match(r"q(\d+)h", freq)
    if match:
        return int(match.group(1))
        
    log.warning(f"Unknown frequency '{frequency}', defaulting to 24 hours.")
    return 24

def generate_tasks_for_order(db: Session, order: MedicationOrder):
    """Generates individual MedicationTask records based on the order's frequency."""
    interval_hours = parse_frequency_hours(order.frequency)
    now = datetime.utcnow()
    end_time = order.end_date if order.end_date else (now + timedelta(days=3))
    
    current_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    tasks_created = 0
    
    while current_time <= end_time:
        task = MedicationTask(
            order_id=order.id,
            scheduled_time=current_time,
            status=TaskStatus.PENDING
        )
        db.add(task)
        current_time += timedelta(hours=interval_hours)
        tasks_created += 1
        
    db.commit()
    log.info(f"Generated {tasks_created} tasks for order {order.id}")

def create_order(db: Session, order_in: MedicationOrderCreate, doctor_id: int) -> MedicationOrder:
    log.info(f"Creating new medication order for patient {order_in.patient_id} by doctor {doctor_id}")
    db_order = MedicationOrder(
        **order_in.model_dump(),
        doctor_id=doctor_id,
        start_date=datetime.utcnow()
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    generate_tasks_for_order(db, db_order)
    return db_order

def get_orders_by_patient(db: Session, patient_id: int) -> List[MedicationOrder]:
    return db.query(MedicationOrder).filter(MedicationOrder.patient_id == patient_id).all()

def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Optional[MedicationOrder]:
    order = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if order:
        order.status = status
        db.commit()
        db.refresh(order)
    return order

# --- Task Management ---
def get_tasks_for_patient(db: Session, patient_id: int) -> List[MedicationTask]:
    """Retrieves all active medication tasks for a specific patient."""
    return db.query(MedicationTask)\
             .join(MedicationOrder)\
             .filter(MedicationOrder.patient_id == patient_id)\
             .order_by(MedicationTask.scheduled_time.asc())\
             .all()

def update_task_status(db: Session, task_id: int, nurse_id: int, status: TaskStatus, notes: Optional[str] = None) -> Optional[MedicationTask]:
    """Updates a medication task (e.g., Nurse administering or skipping it)."""
    task = db.query(MedicationTask).filter(MedicationTask.id == task_id).first()
    if task:
        task.status = status
        task.assigned_nurse_id = nurse_id
        task.notes = notes
        
        if status == TaskStatus.ADMINISTERED:
            task.administered_time = datetime.utcnow()
            
        # Escalation Logic: If skipped, we will eventually trigger a notification to the doctor here.
        if status == TaskStatus.SKIPPED:
            log.warning(f"ESCALATION: Task {task.id} was skipped by Nurse {nurse_id}. Reason: {notes}")
            
        db.commit()
        db.refresh(task)
    return task
