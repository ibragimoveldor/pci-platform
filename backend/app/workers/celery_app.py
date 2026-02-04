"""Celery application configuration for background tasks."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "pci_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks.analysis"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    result_expires=86400,
    task_routes={
        "app.workers.tasks.analysis.*": {"queue": "analysis"},
    },
    task_default_retry_delay=60,
    task_max_retries=3,
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "app.workers.tasks.analysis.cleanup_old_results",
            "schedule": 3600.0,
        },
    },
)
