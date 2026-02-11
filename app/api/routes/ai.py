"""AI feature API routes (cover letter, ATS check, scoring, skill gaps)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sqlalchemy import func as sa_func

from app.api.schemas import ATSCheckRequest, LearningItemOut, LearningItemUpdate, SkillSummary
from app.database import get_db
from app.models import Job, LearningItem, UserProfile

router = APIRouter(prefix="/jobs", tags=["ai"])


@router.post("/{job_id}/cover-letter")
def generate_cover_letter(job_id: UUID, db: Session = Depends(get_db)) -> dict:
    """Generate a cover letter for a specific job."""
    from app.ai.cover_letter import generate

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        cover_letter = generate(job, profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"cover_letter": cover_letter}


@router.post("/{job_id}/ats-check")
def ats_check(
    job_id: UUID,
    body: ATSCheckRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Check resume ATS compatibility against a job."""
    from app.ai.ats_checker import check_resume

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        result = check_resume(job, body.resume_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.post("/score")
def score_jobs(db: Session = Depends(get_db)) -> dict:
    """Score all unscored jobs."""
    from app.ai.matcher import score_new_jobs

    scored = score_new_jobs(db)
    return {"scored": scored}


@router.post("/{job_id}/skill-gaps", response_model=list[LearningItemOut])
def analyze_skill_gaps_endpoint(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> list[LearningItem]:
    """Analyze skill gaps for a job and save learning items."""
    from app.ai.skill_gap import analyze_skill_gaps

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Delete existing items for this job before regenerating
    db.query(LearningItem).filter(LearningItem.job_id == job_id).delete()

    try:
        items_data = analyze_skill_gaps(job, profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    learning_items = []
    for item in items_data:
        li = LearningItem(
            job_id=job.id,
            skill=item.get("skill", "Unknown")[:100],
            detail=item.get("detail", "")[:500],
            category=item.get("category", "Other")[:50],
        )
        db.add(li)
        learning_items.append(li)

    db.commit()
    for li in learning_items:
        db.refresh(li)

    return learning_items


@router.get("/{job_id}/learning-items", response_model=list[LearningItemOut])
def get_learning_items(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> list[LearningItem]:
    """Get all learning items for a job."""
    return (
        db.query(LearningItem)
        .filter(LearningItem.job_id == job_id)
        .order_by(LearningItem.category, LearningItem.skill)
        .all()
    )


@router.get("/learning-items/summary", response_model=list[SkillSummary])
def get_learning_summary(db: Session = Depends(get_db)) -> list[dict]:
    """Aggregated skill gap summary across all jobs, sorted by job count descending."""
    rows = (
        db.query(
            LearningItem.skill,
            LearningItem.category,
            sa_func.count(sa_func.distinct(LearningItem.job_id)).label("job_count"),
            sa_func.bool_or(LearningItem.is_known).label("is_known"),
            sa_func.array_agg(sa_func.distinct(LearningItem.detail)).label("details"),
        )
        .group_by(LearningItem.skill, LearningItem.category)
        .order_by(sa_func.count(sa_func.distinct(LearningItem.job_id)).desc(), LearningItem.skill)
        .all()
    )
    return [
        {
            "skill": r.skill,
            "category": r.category,
            "job_count": r.job_count,
            "is_known": r.is_known or False,
            "details": r.details or [],
        }
        for r in rows
    ]


@router.patch("/learning-items/{item_id}", response_model=LearningItemOut)
def toggle_learning_item(
    item_id: UUID,
    body: LearningItemUpdate,
    db: Session = Depends(get_db),
) -> LearningItem:
    """Toggle a learning item's is_known status."""
    item = db.query(LearningItem).filter(LearningItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Learning item not found")
    item.is_known = body.is_known
    db.commit()
    db.refresh(item)
    return item
