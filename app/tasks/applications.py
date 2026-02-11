"""Celery tasks for mass application processing."""

import json
import time

import redis
import structlog

from app.ai.cover_letter import generate
from app.ai.skill_gap import analyze_skill_gaps
from app.config import get_settings
from app.database import SessionLocal
from app.models import Application, ApplicationStatus, Job, JobStatus, LearningItem, UserProfile
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _update_progress(r: redis.Redis, key: str, data: dict) -> None:
    """Write progress to Redis with 1-hour TTL."""
    r.set(key, json.dumps(data), ex=3600)


@celery_app.task(bind=True)
def mass_apply_task(self, job_ids: list[str]) -> dict:
    """Apply to multiple jobs with AI-generated cover letters.

    Stores per-job progress in Redis so the frontend can poll status.
    """
    settings = get_settings()
    r = redis.from_url(settings.redis_url)
    progress_key = f"mass_apply:{self.request.id}"

    progress = {
        "total": len(job_ids),
        "completed": 0,
        "failed": 0,
        "current_job": None,
        "results": [],
        "done": False,
    }
    _update_progress(r, progress_key, progress)

    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            progress["done"] = True
            progress["failed"] = len(job_ids)
            _update_progress(r, progress_key, progress)
            return progress

        for job_id in job_ids:
            job = db.query(Job).filter(Job.id == job_id).first()

            if not job:
                progress["results"].append({
                    "job_id": job_id,
                    "job_title": "Unknown",
                    "status": "failed",
                    "error": "Job not found",
                })
                progress["failed"] += 1
                _update_progress(r, progress_key, progress)
                continue

            if job.status == JobStatus.APPLIED:
                progress["results"].append({
                    "job_id": job_id,
                    "job_title": job.title,
                    "status": "skipped",
                    "error": "Already applied",
                })
                progress["completed"] += 1
                _update_progress(r, progress_key, progress)
                continue

            progress["current_job"] = f"{job.title} at {job.company}"
            _update_progress(r, progress_key, progress)

            try:
                # Generate cover letter
                cover_letter = generate(job, profile)

                # Create application record
                application = Application(
                    job_id=job.id,
                    cover_letter=cover_letter,
                    status=ApplicationStatus.APPLIED,
                )
                db.add(application)
                job.status = JobStatus.APPLIED
                db.commit()

                progress["results"].append({
                    "job_id": job_id,
                    "job_title": job.title,
                    "status": "done",
                })
                progress["completed"] += 1

                # Analyze skill gaps in background (best-effort)
                try:
                    items = analyze_skill_gaps(job, profile)
                    for item in items:
                        db.add(LearningItem(
                            job_id=job.id,
                            skill=item.get("skill", "Unknown"),
                            detail=item.get("detail", ""),
                            category=item.get("category", "Other"),
                        ))
                    db.commit()
                except Exception:
                    logger.warning("skill_gap.failed", job_id=job_id, exc_info=True)
                    db.rollback()

            except Exception as e:
                db.rollback()
                progress["results"].append({
                    "job_id": job_id,
                    "job_title": job.title,
                    "status": "failed",
                    "error": str(e)[:200],
                })
                progress["failed"] += 1
                logger.error("mass_apply.job_failed", job_id=job_id, error=str(e))

            _update_progress(r, progress_key, progress)

            # Rate-limit Claude API calls
            time.sleep(1)

    finally:
        db.close()

    progress["current_job"] = None
    progress["done"] = True
    _update_progress(r, progress_key, progress)

    logger.info(
        "mass_apply.completed",
        total=progress["total"],
        completed=progress["completed"],
        failed=progress["failed"],
    )
    return progress
