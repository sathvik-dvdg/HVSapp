import logging
from datetime import datetime, timedelta
from src.tasks.celery_app import celery
from src.db.session import SessionLocal
from src.modules.medication.models import MedicationTask, TaskStatus

log = logging.getLogger(__name__)

@celery.task(name="src.tasks.medication_tasks.escalate_overdue_medications")
def escalate_overdue_medications():
    """
    Scans for pending medication tasks that are past their scheduled time
    by 30 minutes and marks them as MISSED.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        threshold_time = now - timedelta(minutes=30)
        
        overdue_tasks = db.query(MedicationTask).filter(
            MedicationTask.status == TaskStatus.PENDING,
            MedicationTask.scheduled_time <= threshold_time
        ).all()
        
        if not overdue_tasks:
            log.info("No overdue medications found.")
            return "No overdue medications"
            
        for task in overdue_tasks:
            log.warning(f"Task {task.id} (Order {task.order_id}) scheduled for {task.scheduled_time} is overdue. Marking as MISSED.")
            task.status = TaskStatus.MISSED
            
        db.commit()
        return f"Escalated {len(overdue_tasks)} overdue tasks."
    except Exception as e:
        log.error(f"Error in escalate_overdue_medications task: {e}")
        db.rollback()
    finally:
        db.close()
