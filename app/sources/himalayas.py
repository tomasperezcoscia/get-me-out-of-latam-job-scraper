"""Himalayas data source — Tier 1 public REST API."""

import asyncio
from datetime import datetime, timezone

import structlog

from app.sources.base import BaseSource
from app.utils.parsers import clean_html, extract_tags, parse_salary

logger = structlog.get_logger(__name__)

API_URL = "https://himalayas.app/jobs/api"
PAGE_SIZE = 20
MAX_PAGES = 10


class HimalayasSource(BaseSource):
    """Fetch jobs from Himalayas public API with offset pagination."""

    @property
    def source_name(self) -> str:
        return "himalayas"

    async def fetch(self) -> list[dict]:
        """Paginate through Himalayas API (limit=20, offset)."""
        all_jobs = []
        offset = 0

        async with self._get_client() as client:
            for _ in range(MAX_PAGES):
                resp = await client.get(
                    API_URL,
                    params={"limit": PAGE_SIZE, "offset": offset},
                )

                if resp.status_code == 429:
                    logger.warning("himalayas.rate_limited", offset=offset)
                    break

                resp.raise_for_status()
                data = resp.json()

                jobs = data.get("jobs", [])
                if not jobs:
                    break

                all_jobs.extend(jobs)
                offset += PAGE_SIZE

                if len(jobs) < PAGE_SIZE:
                    break

                await asyncio.sleep(2)  # Respect rate limits

        return all_jobs

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize a Himalayas job entry."""
        title = raw_job.get("title", "").strip()
        company = raw_job.get("companyName", "").strip()
        description = raw_job.get("description", "")

        if not title or not company:
            return None

        # URL: prefer guid (himalayas page), then applicationLink
        url = raw_job.get("guid") or raw_job.get("applicationLink", "")
        if not url:
            return None

        description_clean = clean_html(description)
        if not description_clean:
            return None

        # Salary
        salary_min = raw_job.get("minSalary")
        salary_max = raw_job.get("maxSalary")
        salary_currency = raw_job.get("currency", "USD")

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

        # Tags from categories
        categories = raw_job.get("categories", [])
        if isinstance(categories, list):
            tags = [c.lower().replace("-", " ") for c in categories if isinstance(c, str)]
        else:
            tags = []
        extracted = extract_tags(f"{title} {description_clean}")
        tags = sorted(set(tags + extracted))

        # Location / timezone
        location_restrictions = raw_job.get("locationRestrictions", [])
        tz = raw_job.get("timezoneRestrictions", [])
        if location_restrictions:
            location = ", ".join(str(r) for r in location_restrictions[:3])
        elif tz:
            tz_strs = [f"UTC{t:+d}" if isinstance(t, int) else str(t) for t in tz[:3]]
            location = f"Remote ({', '.join(tz_strs)})"
        else:
            location = "Remote (Worldwide)"

        # Date — pubDate is a Unix timestamp (integer)
        posted_at = None
        pub_date = raw_job.get("pubDate")
        if pub_date:
            try:
                posted_at = datetime.fromtimestamp(int(pub_date), tz=timezone.utc)
            except (ValueError, TypeError, OSError):
                pass

        return {
            "title": title,
            "company": company,
            "location": location,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": salary_currency or "USD",
            "description": description_clean,
            "requirements": None,
            "url": url,
            "posted_at": posted_at,
            "tags": tags,
        }
