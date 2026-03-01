from celery import Celery

from app.core.settings import settings

celery_app = Celery(
    "saf",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    task_routes={
        "app.infra.tasks.ocr_process_job": {"queue": "ocr"},
        "app.infra.tasks.*": {"queue": "default"},
    },
    beat_schedule={
        "compliance-scan-daily": {
            "task": "app.infra.tasks.compliance_scan_daily",
            "schedule": 86400.0,  # 24h
        },
        "send-due-reminders-daily": {
            "task": "app.infra.tasks.send_due_reminders_daily",
            "schedule": 86400.0,
        },
    },
)
