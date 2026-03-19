# app/services/task_service.py
import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

# Import project components
from app.models.task import NurseTask, TaskStatus
from app.schemas.task import TaskCreate
from app.models.encounter import Encounter
from app.models.user import User, UserRole

log = logging.getLogger(__name__)

# --- Task Creation ---
def create_task(db: Session, *, task_in: TaskCreate) -> Optional[NurseTask]:
    """
    Creates a new nurse task for a specific encounter.
    Validates encounter existence and optionally assigned nurse existence/role.
    """
    log.info(f"Attempting to create task for encounter ID: {task_in.encounter_id}")

    # 1. Check if encounter exists
    encounter = db.query(Encounter).filter(Encounter.id == task_in.encounter_id).first()
    if not encounter:
        log.error(f"Cannot create task: Encounter {task_in.encounter_id} not found.")
        return None

    # 2. Check if assigned nurse exists and has the correct role (optional)
    if task_in.assigned_nurse_id is not None:
        assigned_nurse = db.query(User).filter(User.id == task_in.assigned_nurse_id).first()
        if not assigned_nurse:
            log.error(f"Cannot create task: Assigned nurse {task_in.assigned_nurse_id} not found.")
            return None
        if assigned_nurse.role != UserRole.NURSE:
            log.error(f"Cannot assign task: User {assigned_nurse.id} is not a nurse.")
            return None

    try:
        db_task = NurseTask(
            description=task_in.description,
            encounter_id=task_in.encounter_id,
            due_at=task_in.due_at,
            assigned_nurse_id=task_in.assigned_nurse_id,
            # status defaults to PENDING in the model
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        log.info(f"Successfully created task ID: {db_task.id} for encounter {task_in.encounter_id}")
        return db_task
    except SQLAlchemyError as e:
        log.error(f"Database error during task creation for encounter {task_in.encounter_id}: {e}", exc_info=True)
        db.rollback()
        return None
    except Exception as e:
        log.error(f"Unexpected error during task creation for encounter {task_in.encounter_id}: {e}", exc_info=True)
        db.rollback()
        return None

# --- Task Retrieval ---
def get_tasks_for_encounter(db: Session, *, encounter_id: int, status_filter: Optional[TaskStatus] = None) -> List[NurseTask]:
    """
    Retrieves all tasks for a given patient encounter, ordered newest first.
    """
    log.debug(f"Querying tasks for encounter ID: {encounter_id} with status filter: {status_filter}")
    query = db.query(NurseTask).filter(NurseTask.encounter_id == encounter_id)
    if status_filter:
        query = query.filter(NurseTask.status == status_filter)
    tasks = query.order_by(desc(NurseTask.created_at)).all()
    log.info(f"Found {len(tasks)} tasks for encounter {encounter_id}.")
    return tasks

def get_tasks_for_nurse(db: Session, *, nurse_id: int, status_filter: Optional[TaskStatus] = TaskStatus.PENDING) -> List[NurseTask]:
    """
    Retrieves tasks assigned to a specific nurse, filtering by status (PENDING by default).
    """
    log.debug(f"Querying tasks for nurse ID: {nurse_id} with status filter: {status_filter}")
    assigned_nurse = db.query(User).filter(User.id == nurse_id).first()
    if not assigned_nurse or assigned_nurse.role not in [UserRole.NURSE, UserRole.ADMIN]:
        log.warning(f"Access denied or invalid ID: User {nurse_id} is not a nurse or does not exist.")
        return []

    query = db.query(NurseTask).filter(NurseTask.assigned_nurse_id == nurse_id)
    if status_filter:
        query = query.filter(NurseTask.status == status_filter)
    tasks = query.order_by(NurseTask.due_at.asc().nullsfirst(), NurseTask.created_at.asc()).all() # Order by due date
    log.info(f"Found {len(tasks)} tasks for nurse {nurse_id}.")
    return tasks

# --- Task Completion ---
def complete_task(db: Session, *, task_id: int, completing_user_id: int) -> Optional[NurseTask]:
    """
    Marks a task as COMPLETED and records the completion timestamp.
    """
    log.info(f"User {completing_user_id} attempting to complete task ID: {task_id}")
    db_task = db.query(NurseTask).filter(NurseTask.id == task_id).first()
    if not db_task:
        log.warning(f"Task ID {task_id} not found for completion attempt.")
        return None
    if db_task.status == TaskStatus.COMPLETED:
        log.warning(f"Task ID {task_id} is already marked complete.")
        return db_task # Return the task as the state is already correct

    try:
        db_task.status = TaskStatus.COMPLETED
        db_task.completed_at = datetime.now(timezone.utc)
        
        # If task was unassigned, assign it to the user who completed it.
        if db_task.assigned_nurse_id is None:
            db_task.assigned_nurse_id = completing_user_id
            log.info(f"Task {task_id} was unassigned; setting completer as assigned nurse.")

        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        log.info(f"Successfully COMPLETED task ID: {db_task.id} by user {completing_user_id}.")
        return db_task
    except SQLAlchemyError as e:
        log.error(f"Database error completing task {task_id}: {e}", exc_info=True)
        db.rollback()
        return None

# --- Automated Task Generation (AI Placeholder) ---
def generate_tasks_from_note(db: Session, *, note_content: str, encounter_id: int) -> List[NurseTask]:
    """
    Parses the clinical note content and automatically generates tasks based on keywords.
    This is a rule-based placeholder for a more advanced AI extraction model.
    """
    log.info(f"Generating tasks from note for encounter {encounter_id}...")
    generated_tasks = []
    
    # Simple keyword-based rules
    keywords = ["check", "monitor", "administer", "give", "verify", "assess"]
    sentences = note_content.split('.')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        lower_sentence = sentence.lower()
        if any(keyword in lower_sentence for keyword in keywords):
            # Create a task for this sentence
            task_in = TaskCreate(
                encounter_id=encounter_id,
                description=sentence,
                due_at=None, # Default to immediate/unspecified
                assigned_nurse_id=None # Unassigned initially
            )
            created_task = create_task(db, task_in=task_in)
            if created_task:
                generated_tasks.append(created_task)
                
    log.info(f"Generated {len(generated_tasks)} tasks from note.")
    return generated_tasks