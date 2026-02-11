"""Resume tailoring using Claude API."""

import anthropic
import structlog

from app.ai.prompts import RESUME_TAILOR_SYSTEM, RESUME_TAILOR_USER
from app.config import get_settings
from app.models import Job, UserProfile

logger = structlog.get_logger(__name__)


def quick_tailor(job: Job, profile: UserProfile, resume_section: str) -> str:
    """Tailor a resume section to match job requirements.

    Args:
        job: Target job listing.
        profile: User profile.
        resume_section: The resume text to tailor.

    Returns:
        Tailored resume section text.
    """
    settings = get_settings()
    if not settings.anthropic_api_key or settings.anthropic_api_key == "sk-ant-xxxxx":
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = RESUME_TAILOR_USER.format(
        title=job.title,
        company=job.company,
        requirements=(job.requirements or job.description or "")[:500],
        resume_section=resume_section,
    )

    logger.info("resume_tailor.generating", job=job.title)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        temperature=0.3,
        system=RESUME_TAILOR_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()
