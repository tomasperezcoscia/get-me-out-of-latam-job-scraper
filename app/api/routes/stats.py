"""Stats API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import StatsOut
from app.database import get_db
from app.models import Job

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)) -> dict:
    """Get aggregated job statistics."""
    total = db.query(func.count(Job.id)).scalar() or 0

    source_rows = (
        db.query(Job.source, func.count(Job.id))
        .group_by(Job.source)
        .all()
    )
    by_source = {src or "unknown": cnt for src, cnt in source_rows}

    status_rows = (
        db.query(Job.status, func.count(Job.id))
        .group_by(Job.status)
        .all()
    )
    by_status = {s.value if hasattr(s, "value") else str(s): cnt for s, cnt in status_rows}

    salary_stats = db.query(
        func.count(Job.id).filter(Job.salary_min.isnot(None)),
        func.avg(Job.salary_min),
        func.avg(Job.salary_max),
    ).first()

    jobs_with_salary = (
        db.query(func.count(Job.id))
        .filter(Job.salary_min.isnot(None))
        .scalar() or 0
    )

    return {
        "total_jobs": total,
        "by_source": by_source,
        "by_status": by_status,
        "jobs_with_salary": jobs_with_salary,
        "avg_salary_min": round(float(salary_stats[1]), 0) if salary_stats[1] else None,
        "avg_salary_max": round(float(salary_stats[2]), 0) if salary_stats[2] else None,
    }
