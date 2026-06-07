import logging

from src.tasks.celery_app import celery
from src.db.session import SessionLocal
from src.modules.medication import service as medication_service

log = logging.getLogger(__name__)

@celery.task(name="src.tasks.medication_tasks.escalate_overdue_medications")
def escalate_overdue_medications():
    """Scans pending medication tasks and emits idempotent escalation events."""
    db = SessionLocal()
    try:
        escalated_count = medication_service.check_medication_tasks(db)
        if escalated_count == 0:
            log.info("No overdue medication escalations required.")
            return "No overdue medication escalations"
        return f"Processed {escalated_count} medication escalations."
    except Exception as e:
        log.error(f"Error in escalate_overdue_medications task: {e}")
        db.rollback()
    finally:
        db.close()


def check_medication_tasks() -> str:
    return escalate_overdue_medications()
