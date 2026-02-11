"""Application tracking API routes."""

import json
from uuid import UUID

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    ApplicationWithJobOut,
    MassApplyProgress,
    MassApplyRequest,
    MassApplyStarted,
)
from app.config import get_settings
from app.database import get_db
from app.models import Application, ApplicationStatus, Job, JobStatus, LearningItem, UserProfile

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

    # Auto-generate skill gap analysis (best-effort, don't block the response)
    try:
        from app.ai.skill_gap import analyze_skill_gaps

        profile = db.query(UserProfile).first()
        if profile:
            existing = db.query(LearningItem).filter(LearningItem.job_id == job.id).count()
            if existing == 0:
                items_data = analyze_skill_gaps(job, profile)
                for item in items_data:
                    db.add(LearningItem(
                        job_id=job.id,
                        skill=item.get("skill", "Unknown")[:100],
                        detail=item.get("detail", "")[:500],
                        category=item.get("category", "Other")[:50],
                    ))
                db.commit()
    except Exception:
        db.rollback()

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


@router.get("/pipeline", response_model=list[ApplicationWithJobOut])
def list_applications_pipeline(
    db: Session = Depends(get_db),
) -> list[dict]:
    """List all applications with job info for the pipeline view."""
    rows = (
        db.query(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return [
        {
            "id": app.id,
            "job_id": app.job_id,
            "job_title": job.title,
            "job_company": job.company,
            "job_url": job.url,
            "job_score": job.match_score,
            "applied_at": app.applied_at,
            "cover_letter": app.cover_letter,
            "resume_version": app.resume_version,
            "status": app.status.value if hasattr(app.status, "value") else app.status,
            "follow_up_date": app.follow_up_date,
            "interview_notes": app.interview_notes,
            "notes": app.notes,
            "created_at": app.created_at,
        }
        for app, job in rows
    ]


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


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: UUID,
    body: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> Application:
    """Update an application's status, notes, or follow-up date."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if body.status is not None:
        application.status = body.status
    if body.notes is not None:
        application.notes = body.notes
    if body.interview_notes is not None:
        application.interview_notes = body.interview_notes
    if body.follow_up_date is not None:
        application.follow_up_date = body.follow_up_date

    db.commit()
    db.refresh(application)
    return application


@router.post("/mass-apply", response_model=MassApplyStarted)
def start_mass_apply(
    body: MassApplyRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Start a mass apply background task (runs in a thread)."""
    from app.tasks.applications import start_mass_apply_thread

    # Validate job_ids exist and aren't already applied
    job_ids_str = [str(jid) for jid in body.job_ids]
    existing = db.query(Job.id).filter(Job.id.in_(body.job_ids)).all()
    if len(existing) != len(body.job_ids):
        raise HTTPException(status_code=400, detail="Some job IDs not found")

    task_id = start_mass_apply_thread(job_ids_str)
    return {"task_id": task_id, "total": len(job_ids_str)}


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
