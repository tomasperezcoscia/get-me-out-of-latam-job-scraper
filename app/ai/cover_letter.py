"""Cover letter generation using Claude API."""

from pathlib import Path

import anthropic
import structlog

from app.ai.prompts import COVER_LETTER_SYSTEM, COVER_LETTER_USER
from app.config import get_settings
from app.models import Job, UserProfile

logger = structlog.get_logger(__name__)

DATA_DIR = Path("data/cover_letters")


def generate(job: Job, profile: UserProfile) -> str:
    """Generate a personalized cover letter for a job application.

    Returns:
        The generated cover letter text.
    """
    settings = get_settings()
    if not settings.anthropic_api_key or settings.anthropic_api_key == "sk-ant-xxxxx":
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = COVER_LETTER_USER.format(
        title=job.title,
        company=job.company,
        description=(job.description or "")[:500],
        requirements=(job.requirements or job.description or "")[:300],
        name=profile.full_name,
        location=profile.location or "Argentina",
        timezone=profile.timezone or "UTC-3",
        years=profile.years_experience or 5,
        skills=", ".join(profile.primary_skills or []),
        bio=profile.bio or "",
    )

    logger.info("cover_letter.generating", job=job.title, company=job.company)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        temperature=0.7,
        system=COVER_LETTER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    cover_letter = message.content[0].text.strip()

    logger.info("cover_letter.generated", length=len(cover_letter))
    return cover_letter


def save_cover_letter(job: Job, cover_letter: str) -> Path:
    """Save a cover letter to data/cover_letters/{job_id}.txt."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / f"{job.id}.txt"
    filepath.write_text(
        f"Cover Letter — {job.title} at {job.company}\n"
        f"{'=' * 60}\n\n"
        f"{cover_letter}\n",
        encoding="utf-8",
    )
    return filepath
