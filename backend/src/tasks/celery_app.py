from celery import Celery
from celery.schedules import crontab
from src.config.settings import settings

celery = Celery(
    "hvs",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['src.tasks.medication_tasks', 'src.tasks.handoff_tasks']
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery.conf.beat_schedule = {
    "medication-escalation-monitor": {
        "task": "src.tasks.medication_tasks.escalate_overdue_medications",
        "schedule": crontab(minute="*/5"),
    },
    "handoff-escalation-monitor": {
        "task": "src.tasks.handoff_tasks.check_pending_handoffs",
        "schedule": crontab(minute="*/30"),
    },
    # "audit-integrity-check": {
    #     "task": "src.tasks.audit_tasks.verify_hash_chain_integrity",
    #     "schedule": crontab(hour=3, minute=0),
    # },
}
