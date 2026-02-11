"""ATS (Applicant Tracking System) compatibility checker using Claude API."""

import json

import anthropic
import structlog

from app.ai.prompts import ATS_CHECKER_SYSTEM, ATS_CHECKER_USER
from app.config import get_settings
from app.models import Job

logger = structlog.get_logger(__name__)


def check_resume(job: Job, resume_text: str) -> dict:
    """Check resume ATS compatibility against a job.

    Returns:
        Dict with keys: ats_score, missing_keywords, present_keywords, suggestions
    """
    settings = get_settings()
    if not settings.anthropic_api_key or settings.anthropic_api_key == "sk-ant-xxxxx":
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = ATS_CHECKER_USER.format(
        title=job.title,
        company=job.company,
        requirements=(job.requirements or job.description or "")[:500],
        resume_text=resume_text[:2000],
    )

    logger.info("ats_checker.analyzing", job=job.title)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        temperature=0.2,
        system=ATS_CHECKER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Try to parse JSON from response
    try:
        # Handle markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text)
    except (json.JSONDecodeError, IndexError):
        result = {
            "ats_score": None,
            "missing_keywords": [],
            "present_keywords": [],
            "suggestions": [response_text],
        }

    return result
