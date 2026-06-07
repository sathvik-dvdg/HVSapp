import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.modules.auth.models import User, UserRole
from src.modules.auth.service import get_user_by_id
from src.modules.audit.service import write_audit_log
from src.modules.patients.encounter_models import Encounter
from src.modules.patients.models import Patient
from src.modules.medication.models import MedicationOrder, MedicationTask, OrderStatus, TaskStatus
from src.modules.medication.schemas import MedicationOrderCreate, MedicationTaskAdminister

log = logging.getLogger(__name__)


class DuplicateAdministrationError(Exception):
    def __init__(self, drug_name: str, last_administered_at: datetime, interval_minutes: int) -> None:
        self.drug_name = drug_name
        self.last_administered_at = last_administered_at
        self.interval_minutes = interval_minutes
        super().__init__(f"Duplicate administration blocked for {drug_name}")

    def as_detail(self) -> dict[str, object]:
        return {
            "code": "DUPLICATE_ADMINISTRATION",
            "drug_name": self.drug_name,
            "last_administered_at": self.last_administered_at.isoformat(),
            "interval_minutes": self.interval_minutes,
        }

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
    raise ValueError(f"Unrecognized frequency: {frequency}")


def _resolve_encounter_id(db: Session, order_in: MedicationOrderCreate) -> int:
    if order_in.encounter_id is not None:
        encounter = db.query(Encounter).filter(Encounter.id == order_in.encounter_id).first()
        if encounter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
        return encounter.id

    encounter = (
        db.query(Encounter)
        .filter(Encounter.patient_id == order_in.patient_id)
        .order_by(Encounter.created_at.desc())
        .first()
    )
    if encounter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found for patient")
    return encounter.id


def expand_medication_order(order: MedicationOrder) -> list[MedicationTask]:
    interval_hours = parse_frequency_hours(order.frequency)
    current_time = order.start_datetime
    if not order.end_datetime:
        max_end = order.start_datetime + timedelta(days=30)
    else:
        max_end = min(order.end_datetime, order.start_datetime + timedelta(days=30))

    tasks: list[MedicationTask] = []
    while current_time <= max_end:
        if len(tasks) >= 1000:
            raise ValueError("Task limit exceeded; split order into shorter durations")
        tasks.append(
            MedicationTask(
                order_id=order.id,
                encounter_id=order.encounter_id,
                scheduled_at=current_time,
                due_by=current_time + timedelta(minutes=30),
                status=TaskStatus.PENDING.value,
            )
        )
        current_time += timedelta(hours=interval_hours)
    return tasks

def create_order(db: Session, order_in: MedicationOrderCreate, doctor_id: int) -> MedicationOrder:
    encounter_id = _resolve_encounter_id(db, order_in)
    log.info("Creating new medication order for encounter %s by doctor %s", encounter_id, doctor_id)
    db_order = MedicationOrder(
        encounter_id=encounter_id,
        ordered_by=doctor_id,
        drug_name=order_in.drug_name,
        dose=order_in.dose,
        route=order_in.route,
        frequency=order_in.frequency,
        start_datetime=order_in.start_datetime or datetime.utcnow(),
        end_datetime=order_in.end_datetime,
        special_instructions=order_in.special_instructions,
        minimum_dose_interval_minutes=order_in.minimum_dose_interval_minutes,
        is_active=True,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    tasks = expand_medication_order(db_order)
    if tasks:
        db.add_all(tasks)
        db.commit()

    return db_order

def get_orders_by_patient(db: Session, patient_id: str) -> List[MedicationOrder]:
    return (
        db.query(MedicationOrder)
        .join(Encounter, Encounter.id == MedicationOrder.encounter_id)
        .filter(Encounter.patient_id == patient_id)
        .order_by(MedicationOrder.created_at.desc())
        .all()
    )

def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Optional[MedicationOrder]:
    order = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if order:
        order.is_active = status == OrderStatus.ACTIVE
        db.commit()
        db.refresh(order)
    return order

def get_tasks_for_patient(db: Session, patient_id: str) -> List[MedicationTask]:
    """Retrieves all active medication tasks for a specific patient."""
    tasks = (
        db.query(MedicationTask)
        .join(Encounter, Encounter.id == MedicationTask.encounter_id)
        .filter(Encounter.patient_id == patient_id)
        .order_by(MedicationTask.scheduled_at.asc())
        .all()
    )
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    for task in tasks:
        order = db.query(MedicationOrder).filter(MedicationOrder.id == task.order_id).first()
        task.patient_id = patient.id if patient else None
        task.patient_name = patient.full_name if patient else None
        task.patient_date_of_birth = patient.date_of_birth if patient else None
        task.bed_number = patient.bed_number if patient else None
        task.drug_name = order.drug_name if order else None
        task.dose = order.dose if order else None
        task.route = order.route if order else None
    return tasks


def _get_task_with_context(db: Session, task_id: int) -> tuple[MedicationTask, MedicationOrder, Encounter, Patient]:
    task = db.query(MedicationTask).filter(MedicationTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    order = db.query(MedicationOrder).filter(MedicationOrder.id == task.order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication order not found")

    encounter = db.query(Encounter).filter(Encounter.id == task.encounter_id).first()
    if encounter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    patient = db.query(Patient).filter(Patient.id == encounter.patient_id).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    return task, order, encounter, patient


def administer_medication_task(
    db: Session,
    task_id: int,
    current_user: User,
    administer_data: MedicationTaskAdminister,
) -> MedicationTask:
    task, order, _encounter, patient = _get_task_with_context(db, task_id)

    if current_user.role not in (UserRole.NURSE, UserRole.ADMIN, UserRole.DOCTOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clinical staff can administer medication")
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive users cannot administer medication")
    if current_user.ward_assignment and patient.ward and current_user.ward_assignment != patient.ward:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "WARD_MISMATCH"},
        )
    if not administer_data.patient_verified or not administer_data.drug_name_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "IDENTITY_VERIFICATION_REQUIRED"},
        )
    if administer_data.override_reason and current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PHYSICIAN_OVERRIDE_REQUIRED"},
        )
    if administer_data.witness_id is not None:
        witness = get_user_by_id(db, user_id=administer_data.witness_id)
        if witness is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Witness not found")
        if witness.role not in [UserRole.NURSE, UserRole.DOCTOR]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Witness must be an active nurse or doctor")
        if not witness.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Witness must be active")
        task.witness_id = witness.id

    administered_at = datetime.utcnow()
    duplicate_task = (
        db.query(MedicationTask)
        .join(MedicationOrder, MedicationOrder.id == MedicationTask.order_id)
        .join(Encounter, Encounter.id == MedicationTask.encounter_id)
        .filter(MedicationTask.id != task.id)
        .filter(MedicationTask.status == TaskStatus.ADMINISTERED.value)
        .filter(MedicationOrder.drug_name == order.drug_name)
        .filter(Encounter.patient_id == patient.id)
        .filter(
            MedicationTask.administered_at
            >= administered_at - timedelta(minutes=order.minimum_dose_interval_minutes)
        )
        .order_by(MedicationTask.administered_at.desc())
        .first()
    )
    if duplicate_task is not None and duplicate_task.administered_at is not None:
        error = DuplicateAdministrationError(
            drug_name=order.drug_name,
            last_administered_at=duplicate_task.administered_at,
            interval_minutes=order.minimum_dose_interval_minutes,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.as_detail())

    task.status = TaskStatus.ADMINISTERED.value
    task.administered_at = administered_at
    task.administered_by = current_user.id
    task.assigned_nurse_id = current_user.id
    task.notes = administer_data.notes
    db.commit()
    db.refresh(task)
    return task


def update_task_status(
    db: Session,
    task_id: int,
    nurse_id: int,
    task_status: TaskStatus,
    notes: Optional[str] = None,
) -> Optional[MedicationTask]:
    task = db.query(MedicationTask).filter(MedicationTask.id == task_id).first()
    if task is None:
        return None

    if task_status == TaskStatus.ADMINISTERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the administer endpoint for medication administration",
        )

    task.status = task_status.value
    task.assigned_nurse_id = nurse_id
    task.notes = notes
    if task_status == TaskStatus.SKIPPED:
        task.skipped_reason = notes
        log.warning("Medication task %s skipped by nurse %s. Reason: %s", task.id, nurse_id, notes)

    db.commit()
    db.refresh(task)
    return task


def check_medication_tasks(db: Session) -> int:
    now = datetime.utcnow()
    escalated_count = 0
    pending_tasks = db.query(MedicationTask).filter(MedicationTask.status == TaskStatus.PENDING.value).all()
    for task in pending_tasks:
        if task.scheduled_at > now:
            continue

        overdue_minutes = int((now - task.scheduled_at).total_seconds() // 60)
        escalation_level = 0
        if overdue_minutes >= 240:
            escalation_level = 4
        elif overdue_minutes >= 120:
            escalation_level = 3
        elif overdue_minutes >= 60:
            escalation_level = 2
        elif overdue_minutes >= 30:
            escalation_level = 1

        if escalation_level == 0:
            continue
        if task.last_escalation_level is not None and task.last_escalation_level >= escalation_level:
            continue

        start_level = (task.last_escalation_level or 0) + 1
        for level in range(start_level, escalation_level + 1):
            write_audit_log(
                db=db,
                user_id=task.assigned_nurse_id,
                action=f"MEDICATION_ESCALATION_L{level}",
                resource_type="medication_task",
                resource_id=str(task.id),
                patient_id=None,
                new_value={
                    "escalation_level": level,
                    "scheduled_at": task.scheduled_at.isoformat(),
                },
            )
            log.warning("Queued medication escalation L%s for task %s", level, task.id)
            task.last_escalation_level = level
            db.add(task)
            db.commit()
            escalated_count += 1
    return escalated_count
