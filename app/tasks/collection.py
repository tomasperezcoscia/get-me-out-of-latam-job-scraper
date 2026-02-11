"""Celery tasks for job collection."""

import asyncio

import structlog

from app.database import SessionLocal
from app.sources import get_all_sources
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.tasks.collection.daily_collect")
def daily_collect() -> dict:
    """Collect jobs from all configured sources."""
    logger.info("task.daily_collect.start")

    sources = get_all_sources()
    results = {}

    for source in sources:
        try:
            jobs = asyncio.run(source.collect())
            inserted = 0
            if jobs:
                db = SessionLocal()
                try:
                    inserted = source.save(jobs, db)
                finally:
                    db.close()

            results[source.source_name] = {
                "fetched": len(jobs),
                "inserted": inserted,
            }
        except Exception:
            logger.exception("task.daily_collect.source_error", source=source.source_name)
            results[source.source_name] = {"fetched": 0, "inserted": 0, "error": True}

    total_fetched = sum(r["fetched"] for r in results.values())
    total_inserted = sum(r["inserted"] for r in results.values())

    logger.info(
        "task.daily_collect.done",
        total_fetched=total_fetched,
        total_inserted=total_inserted,
    )
    return results
