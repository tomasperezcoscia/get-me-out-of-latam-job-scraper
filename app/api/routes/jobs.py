"""Job listing API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import JobListResponse, JobOut, JobStatusUpdate
from app.database import get_db
from app.models import Job, JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobListResponse)
def list_jobs(
    status: str | None = None,
    source: str | None = None,
    min_score: float | None = None,
    min_salary: int | None = None,
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """List jobs with filters and pagination."""
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    if source:
        query = query.filter(Job.source == source)
    if min_score is not None:
        query = query.filter(Job.match_score >= min_score)
    if min_salary is not None:
        query = query.filter(
            (Job.salary_min >= min_salary) | (Job.salary_min.is_(None))
        )
    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") | Job.company.ilike(f"%{search}%")
        )

    total = query.count()

    items = (
        query.order_by(Job.match_score.desc().nulls_last(), Job.scraped_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: UUID, db: Session = Depends(get_db)) -> Job:
    """Get a specific job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}/status")
def update_job_status(
    job_id: UUID,
    update: JobStatusUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Update a job's status."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus(update.status)
    if update.notes:
        job.notes = update.notes
    db.commit()

    return {"id": str(job.id), "status": job.status.value}
