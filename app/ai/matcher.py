"""Hybrid job matching: semantic similarity + rule-based scoring."""

import re

import numpy as np
import structlog
from sqlalchemy.orm import Session

from app.ai.embeddings import embed_text
from app.models import Job, UserProfile

logger = structlog.get_logger(__name__)

# Skill aliases for fuzzy matching
SKILL_ALIASES = {
    "ruby on rails": ["rails", "ruby", "ror"],
    "golang": ["go"],
    "go": ["golang"],
    "react": ["reactjs", "react.js"],
    "node.js": ["nodejs", "node"],
    "next.js": ["nextjs", "next"],
    "postgresql": ["postgres", "psql"],
    "typescript": ["ts"],
    "javascript": ["js"],
    "python": ["py"],
    "kubernetes": ["k8s"],
    "c#": ["csharp", "dotnet", ".net"],
}

SENIOR_KEYWORDS = {"senior", "lead", "principal", "staff", "architect", "sr.", "sr "}
JUNIOR_KEYWORDS = {"junior", "entry", "intern", "jr.", "jr ", "trainee", "graduate"}

LATAM_KEYWORDS = {
    "latam", "latin america", "south america", "argentina", "brazil", "mexico",
    "colombia", "chile", "americas",
}
REMOTE_KEYWORDS = {"remote", "anywhere", "worldwide", "global", "distributed"}


class JobMatcher:
    """Hybrid scoring engine combining semantic and rule-based signals."""

    def __init__(self, profile: UserProfile | None = None):
        self._profile = profile
        self._profile_embedding: list[float] | None = None

    def _get_profile_embedding(self) -> list[float]:
        """Generate or return cached profile embedding."""
        if self._profile_embedding is None:
            p = self._profile
            text = (
                f"{p.bio or ''} "
                f"Skills: {', '.join(p.primary_skills or [])}. "
                f"{p.years_experience or 0} years experience. "
                f"Location: {p.location or 'Argentina'}."
            )
            self._profile_embedding = embed_text(text)
        return self._profile_embedding

    def _semantic_score(self, job: Job) -> float:
        """Compute semantic similarity (0-40 points)."""
        if job.embedding is None:
            return 20.0  # Default mid-score if no embedding

        profile_vec = np.array(self._get_profile_embedding())
        job_vec = np.array(list(job.embedding))

        # Cosine similarity (vectors are already normalized)
        similarity = float(np.dot(profile_vec, job_vec))
        return max(0.0, min(40.0, similarity * 40.0))

    def _skills_score(self, job: Job) -> float:
        """Compute skills match (0-30 points)."""
        if not self._profile or not self._profile.primary_skills:
            return 15.0

        job_text = f"{job.title} {job.description or ''} {job.requirements or ''}".lower()
        job_tags = set(t.lower() for t in (job.tags or []))

        profile_skills = [s.lower() for s in self._profile.primary_skills]
        matched = 0
        total = len(profile_skills)

        for skill in profile_skills:
            # Exact match in text or tags
            if skill in job_text or skill in job_tags:
                matched += 1
                continue

            # Check aliases
            aliases = SKILL_ALIASES.get(skill, [])
            if any(a in job_text or a in job_tags for a in aliases):
                matched += 0.7
                continue

        if total == 0:
            return 15.0

        return min(30.0, (matched / total) * 30.0)

    def _salary_score(self, job: Job) -> float:
        """Compute salary match (0-15 points)."""
        if not self._profile:
            return 10.0

        desired_min = self._profile.desired_salary_min or 50000

        if job.salary_min is None and job.salary_max is None:
            return 10.0  # Benefit of the doubt

        if job.salary_max and job.salary_max < desired_min:
            return 0.0

        if job.salary_min and job.salary_min >= desired_min:
            return 15.0

        # Partial match
        return 7.0

    def _seniority_score(self, job: Job) -> float:
        """Compute seniority match (0-10 points)."""
        title_lower = job.title.lower()
        desc_lower = (job.description or "").lower()[:500]
        combined = f"{title_lower} {desc_lower}"

        years = (self._profile.years_experience or 5) if self._profile else 5

        is_senior = any(kw in combined for kw in SENIOR_KEYWORDS)
        is_junior = any(kw in combined for kw in JUNIOR_KEYWORDS)

        if is_senior and years >= 4:
            return 10.0
        elif is_senior and years < 4:
            return 3.0
        elif is_junior:
            return 2.0
        else:
            return 6.0  # Mid-level / unspecified

    def _location_score(self, job: Job) -> float:
        """Compute location/timezone bonus (0-5 points)."""
        location_lower = (job.location or "").lower()
        title_lower = job.title.lower()
        combined = f"{location_lower} {title_lower}"

        if any(kw in combined for kw in LATAM_KEYWORDS):
            return 5.0
        if any(kw in combined for kw in REMOTE_KEYWORDS):
            return 5.0
        if "us timezone" in combined or "est" in combined or "pst" in combined:
            return 3.0
        if "eu only" in combined or "europe only" in combined:
            return 0.0

        return 3.0  # Default for unspecified

    def score_job(self, job: Job) -> float:
        """Compute total match score (0-100)."""
        semantic = self._semantic_score(job)
        skills = self._skills_score(job)
        salary = self._salary_score(job)
        seniority = self._seniority_score(job)
        location = self._location_score(job)

        return round(semantic + skills + salary + seniority + location, 1)

    def explain_score(self, job: Job) -> dict:
        """Return a breakdown of the score components."""
        return {
            "total": self.score_job(job),
            "semantic": round(self._semantic_score(job), 1),
            "skills": round(self._skills_score(job), 1),
            "salary": round(self._salary_score(job), 1),
            "seniority": round(self._seniority_score(job), 1),
            "location": round(self._location_score(job), 1),
        }

    def batch_score(self, jobs: list[Job]) -> list[tuple[Job, float]]:
        """Score a list of jobs and return sorted by score (highest first)."""
        scored = [(job, self.score_job(job)) for job in jobs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored


def score_new_jobs(db: Session, limit: int = 500) -> int:
    """Score all unscored jobs in the database.

    Returns:
        Number of jobs scored.
    """
    profile = db.query(UserProfile).first()
    if not profile:
        logger.warning("scorer.no_profile", msg="No user profile found")
        return 0

    jobs = (
        db.query(Job)
        .filter(Job.match_score.is_(None))
        .order_by(Job.scraped_at.desc())
        .limit(limit)
        .all()
    )

    if not jobs:
        logger.info("scorer.none_needed")
        return 0

    logger.info("scorer.scoring", count=len(jobs))
    matcher = JobMatcher(profile)

    for job in jobs:
        job.match_score = matcher.score_job(job)

    db.commit()
    logger.info("scorer.done", scored=len(jobs))
    return len(jobs)
