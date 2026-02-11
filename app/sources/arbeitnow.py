"""Arbeitnow data source — Tier 1 public JSON API."""

import asyncio
from datetime import datetime, timezone

import structlog

from app.sources.base import BaseSource
from app.utils.parsers import clean_html, extract_tags

logger = structlog.get_logger(__name__)

API_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES = 5


class ArbeitnowSource(BaseSource):
    """Fetch jobs from Arbeitnow's public API with pagination."""

    @property
    def source_name(self) -> str:
        return "arbeitnow"

    async def fetch(self) -> list[dict]:
        """Paginate through Arbeitnow API results."""
        all_jobs = []
        page = 1

        async with self._get_client() as client:
            while page <= MAX_PAGES:
                resp = await client.get(API_URL, params={"page": page})
                resp.raise_for_status()
                data = resp.json()

                jobs = data.get("data", [])
                if not jobs:
                    break

                all_jobs.extend(jobs)

                # Check if there are more pages
                links = data.get("links", {})
                if not links.get("next"):
                    break

                page += 1
                await asyncio.sleep(1)  # Be polite

        return all_jobs

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize an Arbeitnow job entry."""
        title = raw_job.get("title", "").strip()
        company = raw_job.get("company_name", "").strip()
        description = raw_job.get("description", "")
        url = raw_job.get("url", "")

        if not title or not company or not url:
            return None

        description_clean = clean_html(description)
        if not description_clean:
            return None

        # Tags from API + extracted
        api_tags = raw_job.get("tags", [])
        if isinstance(api_tags, list):
            tags = [t.lower().strip() for t in api_tags if isinstance(t, str)]
        else:
            tags = []
        extracted = extract_tags(f"{title} {description_clean}")
        tags = sorted(set(tags + extracted))

        # Location
        location = raw_job.get("location", "Remote")
        is_remote = raw_job.get("remote", False)

        # Parse created_at
        posted_at = None
        created = raw_job.get("created_at")
        if created:
            try:
                posted_at = datetime.fromtimestamp(int(created), tz=timezone.utc)
            except (ValueError, TypeError, OSError):
                pass

        return {
            "title": title,
            "company": company,
            "location": location or "Remote",
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "EUR",
            "description": description_clean,
            "requirements": None,
            "url": url,
            "posted_at": posted_at,
            "is_remote": bool(is_remote),
            "tags": tags,
        }
