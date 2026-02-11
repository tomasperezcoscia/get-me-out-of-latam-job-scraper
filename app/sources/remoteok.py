"""RemoteOK data source — Tier 1 public JSON API."""

from datetime import datetime, timezone

import structlog

from app.sources.base import BaseSource
from app.utils.parsers import clean_html, extract_tags

logger = structlog.get_logger(__name__)

API_URL = "https://remoteok.com/api"


class RemoteOKSource(BaseSource):
    """Fetch jobs from RemoteOK's public JSON API."""

    @property
    def source_name(self) -> str:
        return "remoteok"

    async def fetch(self) -> list[dict]:
        """GET https://remoteok.com/api — returns JSON array, first item is metadata."""
        async with self._get_client() as client:
            resp = await client.get(API_URL)
            resp.raise_for_status()
            data = resp.json()

        # First item is metadata/legal notice — skip it
        if data and isinstance(data, list) and isinstance(data[0], dict):
            if "legal" in data[0] or "0" in data[0]:
                data = data[1:]

        return data

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize a RemoteOK job entry."""
        title = raw_job.get("position", "").strip()
        company = raw_job.get("company", "").strip()
        description = raw_job.get("description", "")
        url = raw_job.get("url", "")

        if not title or not company or not url:
            return None

        # Ensure absolute URL
        if url.startswith("/"):
            url = f"https://remoteok.com{url}"

        # Clean HTML description
        description_clean = clean_html(description)
        if not description_clean:
            return None

        # Parse salary
        salary_min = raw_job.get("salary_min")
        salary_max = raw_job.get("salary_max")
        if salary_min:
            try:
                salary_min = int(salary_min)
            except (ValueError, TypeError):
                salary_min = None
        if salary_max:
            try:
                salary_max = int(salary_max)
            except (ValueError, TypeError):
                salary_max = None

        # Tags from API + extracted from description
        api_tags = raw_job.get("tags", [])
        if isinstance(api_tags, list):
            tags = [t.lower().strip() for t in api_tags if isinstance(t, str)]
        else:
            tags = []
        extracted = extract_tags(f"{title} {description_clean}")
        tags = sorted(set(tags + extracted))

        # Parse date
        posted_at = None
        date_str = raw_job.get("date")
        if date_str:
            try:
                posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        location = raw_job.get("location", "Remote")

        return {
            "title": title,
            "company": company,
            "location": location or "Remote",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": "USD",
            "description": description_clean,
            "requirements": None,
            "url": url,
            "posted_at": posted_at,
            "tags": tags,
        }
