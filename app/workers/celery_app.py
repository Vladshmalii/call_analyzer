from celery import Celery
from app.core.config.settings import settings

celery_app = Celery(
    "call_qc_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.transcribe_call_task": {"queue": "transcription"},
        "app.workers.tasks.download_call_task": {"queue": "general"},
        "app.workers.tasks.analyze_call_task": {"queue": "general"},
        "app.workers.tasks.sync_sheets_task": {"queue": "general"},
        "app.workers.tasks.scan_drive_task": {"queue": "general"}
    }
)
