"""Celery application configuration with beat schedule."""

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "jobhunter",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.collection", "app.tasks.scoring", "app.tasks.notifications", "app.tasks.applications"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,
    beat_schedule={
        "daily-collect": {
            "task": "app.tasks.collection.daily_collect",
            "schedule": crontab(hour=2, minute=0),  # 02:00 ART
        },
        "daily-embed-score": {
            "task": "app.tasks.scoring.daily_embed_score",
            "schedule": crontab(hour=3, minute=0),  # 03:00 ART
        },
        "daily-digest": {
            "task": "app.tasks.notifications.daily_digest",
            "schedule": crontab(hour=9, minute=0),  # 09:00 ART
        },
    },
)
