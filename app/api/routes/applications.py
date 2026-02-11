"""Application tracking API routes."""

import json
from uuid import UUID

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApplicationCreate,
    ApplicationOut,
    MassApplyProgress,
    MassApplyRequest,
    MassApplyStarted,
)
from app.config import get_settings
from app.database import get_db
from app.models import Application, ApplicationStatus, Job, JobStatus

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/", response_model=ApplicationOut)
def create_application(
    body: ApplicationCreate,
    db: Session = Depends(get_db),
) -> Application:
    """Create a new application and set job status to APPLIED."""
    job = db.query(Job).filter(Job.id == body.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    application = Application(
        job_id=body.job_id,
        cover_letter=body.cover_letter,
        resume_version=body.resume_version,
        status=ApplicationStatus.APPLIED,
    )
    db.add(application)

    job.status = JobStatus.APPLIED
    db.commit()
    db.refresh(application)

    return application


@router.get("/", response_model=list[ApplicationOut])
def list_applications(
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[Application]:
    """List all applications with optional status filter."""
    query = db.query(Application)
    if status:
        query = query.filter(Application.status == status)
    return query.order_by(Application.applied_at.desc()).all()


@router.get("/by-job/{job_id}", response_model=ApplicationOut)
def get_application_by_job(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> Application:
    """Get the application for a specific job."""
    application = (
        db.query(Application)
        .filter(Application.job_id == job_id)
        .order_by(Application.applied_at.desc())
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="No application found for this job")
    return application


@router.post("/mass-apply", response_model=MassApplyStarted)
def start_mass_apply(
    body: MassApplyRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Start a mass apply background task."""
    from app.tasks.applications import mass_apply_task

    # Validate job_ids exist and aren't already applied
    job_ids_str = [str(jid) for jid in body.job_ids]
    existing = db.query(Job.id).filter(Job.id.in_(body.job_ids)).all()
    if len(existing) != len(body.job_ids):
        raise HTTPException(status_code=400, detail="Some job IDs not found")

    result = mass_apply_task.delay(job_ids_str)
    return {"task_id": result.id, "total": len(job_ids_str)}


@router.get("/mass-apply/{task_id}", response_model=MassApplyProgress)
def get_mass_apply_progress(task_id: str) -> dict:
    """Poll progress of a mass apply task."""
    settings = get_settings()
    r = redis.from_url(settings.redis_url)
    raw = r.get(f"mass_apply:{task_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Task not found or expired")
    progress = json.loads(raw)
    progress["task_id"] = task_id
    return progress
