import logging

from sqlalchemy import inspect, text

from src.db.session import SessionLocal
from src.modules.audit.service import write_audit_log
from src.tasks.celery_app import celery

log = logging.getLogger(__name__)


@celery.task(name="src.tasks.handoff_tasks.check_pending_handoffs")
def check_pending_handoffs() -> str:
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        if "handoff_sessions" not in inspector.get_table_names():
            log.warning("handoff_sessions table is not present; skipping handoff escalation checks.")
            return "handoff_sessions table not present"

        rows = db.execute(
            text(
                "SELECT id, encounter_id, COALESCE(last_escalation_level, 0) AS last_escalation_level "
                "FROM handoff_sessions WHERE status != 'ACCEPTED'"
            )
        ).mappings().all()

        for row in rows:
            write_audit_log(
                db=db,
                action="HANDOFF_ESCALATION_SCAN",
                resource_type="handoff_session",
                resource_id=str(row["id"]),
                patient_id=None,
                new_value={
                    "encounter_id": row["encounter_id"],
                    "last_escalation_level": row["last_escalation_level"],
                },
            )
        return f"Scanned {len(rows)} pending handoff sessions"
    except Exception as error:
        db.rollback()
        log.error("Failed to scan pending handoffs: %s", error, exc_info=True)
        raise
    finally:
        db.close()
