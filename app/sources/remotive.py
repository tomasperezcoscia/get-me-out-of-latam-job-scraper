"""Remotive data source — Tier 1 public REST API (2 req/min limit)."""

from datetime import datetime

import structlog

from app.sources.base import BaseSource
from app.utils.parsers import clean_html, extract_tags, parse_salary

logger = structlog.get_logger(__name__)

API_URL = "https://remotive.com/api/remote-jobs"


class RemotiveSource(BaseSource):
    """Fetch jobs from Remotive's public API.

    Rate limit: 2 requests/minute, max 4 requests/day recommended.
    We make a single request to avoid hitting limits.
    """

    @property
    def source_name(self) -> str:
        return "remotive"

    async def fetch(self) -> list[dict]:
        """Single request to Remotive API — returns up to ~300 software-dev jobs."""
        async with self._get_client() as client:
            resp = await client.get(
                API_URL,
                params={"category": "software-dev", "limit": 300},
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("jobs", [])

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize a Remotive job entry."""
        title = raw_job.get("title", "").strip()
        company = raw_job.get("company_name", "").strip()
        description = raw_job.get("description", "")
        url = raw_job.get("url", "")

        if not title or not company or not url:
            return None

        description_clean = clean_html(description)
        if not description_clean:
            return None

        # Salary (Remotive provides a text field like "$60,000 - $80,000")
        salary_text = raw_job.get("salary", "")
        salary_min, salary_max, salary_currency = parse_salary(salary_text)

        # Tags from API + extracted
        api_tags = raw_job.get("tags", [])
        if isinstance(api_tags, list):
            tags = [t.lower().strip() for t in api_tags if isinstance(t, str)]
        else:
            tags = []
        extracted = extract_tags(f"{title} {description_clean}")
        tags = sorted(set(tags + extracted))

        # Location
        candidate_locations = raw_job.get("candidate_required_location", "")
        location = candidate_locations if candidate_locations else "Remote"

        # Date
        posted_at = None
        pub_date = raw_job.get("publication_date")
        if pub_date:
            try:
                posted_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Job type
        job_type = raw_job.get("job_type", "")

        return {
            "title": title,
            "company": company,
            "location": location,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": salary_currency,
            "description": description_clean,
            "requirements": None,
            "url": url,
            "posted_at": posted_at,
            "tags": tags,
        }
