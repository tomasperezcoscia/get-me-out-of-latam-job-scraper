"""AI-powered skill gap analysis using Claude API."""

import json

import anthropic
import structlog

from app.ai.prompts import SKILL_GAP_SYSTEM, SKILL_GAP_USER
from app.config import get_settings
from app.models import Job, UserProfile

logger = structlog.get_logger(__name__)


def analyze_skill_gaps(job: Job, profile: UserProfile) -> list[dict]:
    """Analyze skill gaps between a job's requirements and the user's profile.

    Returns:
        List of dicts with keys: skill, detail, category.
    """
    settings = get_settings()
    if not settings.anthropic_api_key or settings.anthropic_api_key == "sk-ant-xxxxx":
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = SKILL_GAP_USER.format(
        title=job.title,
        company=job.company,
        requirements=(job.requirements or job.description or "")[:1500],
        skills=", ".join(profile.primary_skills or []),
        years=profile.years_experience or 5,
        bio=profile.bio or "",
    )

    logger.info("skill_gap.analyzing", job=job.title, company=job.company)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0.4,
        system=SKILL_GAP_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Parse JSON — handle potential markdown fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    items = json.loads(raw)
    logger.info("skill_gap.analyzed", count=len(items))
    return items
