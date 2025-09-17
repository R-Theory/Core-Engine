from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "core_engine",
    broker=settings.REDIS_URL.replace("/0", "/1"),  # Use different Redis DB for Celery
    backend=settings.REDIS_URL.replace("/0", "/2"),  # Use different Redis DB for results
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.ai_processing.*": {"queue": "ai_queue"},
    "app.tasks.plugin_sync.*": {"queue": "plugin_queue"},
    "app.tasks.workflow_execution.*": {"queue": "workflow_queue"},
}

# Periodic tasks
celery_app.conf.beat_schedule = {
    "sync-canvas-data": {
        "task": "app.tasks.plugin_sync.sync_all_canvas_data",
        "schedule": 3600.0,  # Every hour
    },
    "sync-github-data": {
        "task": "app.tasks.plugin_sync.sync_all_github_data",
        "schedule": 7200.0,  # Every 2 hours
    },
}