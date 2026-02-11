"""Celery tasks for job scoring and embedding."""

import structlog

from app.database import SessionLocal
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.tasks.scoring.daily_embed_score")
def daily_embed_score() -> dict:
    """Generate embeddings and score new jobs."""
    from app.ai.embeddings import embed_new_jobs
    from app.ai.matcher import score_new_jobs

    logger.info("task.daily_embed_score.start")

    db = SessionLocal()
    try:
        embedded = embed_new_jobs(db, limit=500)
        scored = score_new_jobs(db, limit=500)
    finally:
        db.close()

    logger.info(
        "task.daily_embed_score.done",
        embedded=embedded,
        scored=scored,
    )
    return {"embedded": embedded, "scored": scored}
