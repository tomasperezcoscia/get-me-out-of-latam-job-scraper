"""Jooble data source — Tier 2 REST API (key required)."""

import structlog

from app.config import get_settings
from app.sources.base import BaseSource
from app.utils.parsers import clean_html, extract_tags, parse_salary

logger = structlog.get_logger(__name__)

API_URL = "https://jooble.org/api/"
SEARCH_KEYWORDS = [
    "remote python developer",
    "remote ruby rails developer",
    "remote golang developer",
    "remote fullstack developer",
    "remote react developer",
]


class JoobleSource(BaseSource):
    """Fetch jobs from Jooble's REST API."""

    @property
    def source_name(self) -> str:
        return "jooble"

    async def fetch(self) -> list[dict]:
        """POST to Jooble API with multiple keyword searches."""
        settings = get_settings()
        if not settings.jooble_api_key:
            logger.warning("jooble.no_api_key", msg="JOOBLE_API_KEY not set, skipping")
            return []

        all_jobs = []
        seen_links = set()

        async with self._get_client() as client:
            for keywords in SEARCH_KEYWORDS:
                try:
                    resp = await client.post(
                        f"{API_URL}{settings.jooble_api_key}",
                        json={
                            "keywords": keywords,
                            "location": "remote",
                            "salary": "50000",
                            "page": 1,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for job in data.get("jobs", []):
                        link = job.get("link", "")
                        if link and link not in seen_links:
                            seen_links.add(link)
                            all_jobs.append(job)

                except Exception:
                    logger.exception("jooble.search.error", keywords=keywords)

        return all_jobs

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize a Jooble job entry."""
        title = raw_job.get("title", "").strip()
        company = raw_job.get("company", "").strip()
        snippet = raw_job.get("snippet", "")
        url = raw_job.get("link", "")

        if not title or not url:
            return None

        company = company or "Unknown"
        description = clean_html(snippet) if snippet else title

        salary_text = raw_job.get("salary", "")
        salary_min, salary_max, currency = parse_salary(salary_text)

        location = raw_job.get("location", "Remote")
        tags = extract_tags(f"{title} {description}")

        return {
            "title": title,
            "company": company,
            "location": location or "Remote",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": currency,
            "description": description,
            "requirements": None,
            "url": url,
            "posted_at": None,
            "tags": tags,
        }
