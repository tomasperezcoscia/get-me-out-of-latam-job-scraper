"""Adzuna data source — Tier 2 REST API (key required)."""

import asyncio
from datetime import datetime

import structlog

from app.config import get_settings
from app.sources.base import BaseSource
from app.utils.parsers import clean_html, extract_tags

logger = structlog.get_logger(__name__)

API_BASE = "https://api.adzuna.com/v1/api/jobs"
COUNTRIES = ["us", "gb", "ca", "de"]
SEARCH_TERMS = ["python developer", "ruby rails developer", "golang developer", "react developer"]


class AdzunaSource(BaseSource):
    """Fetch jobs from Adzuna's multi-country API."""

    @property
    def source_name(self) -> str:
        return "adzuna"

    async def fetch(self) -> list[dict]:
        """Search across multiple countries and keywords."""
        settings = get_settings()
        if not settings.adzuna_app_id or not settings.adzuna_api_key:
            logger.warning("adzuna.no_api_key", msg="ADZUNA_APP_ID/KEY not set, skipping")
            return []

        all_jobs = []
        seen_ids = set()

        async with self._get_client() as client:
            for country in COUNTRIES:
                for term in SEARCH_TERMS:
                    try:
                        resp = await client.get(
                            f"{API_BASE}/{country}/search/1",
                            params={
                                "app_id": settings.adzuna_app_id,
                                "app_key": settings.adzuna_api_key,
                                "what": term,
                                "where": "remote",
                                "salary_min": 50000,
                                "full_time": 1,
                                "results_per_page": 50,
                            },
                        )
                        resp.raise_for_status()
                        data = resp.json()

                        for job in data.get("results", []):
                            job_id = job.get("id")
                            if job_id and job_id not in seen_ids:
                                seen_ids.add(job_id)
                                job["_country"] = country
                                all_jobs.append(job)

                    except Exception:
                        logger.exception(
                            "adzuna.search.error", country=country, term=term
                        )

                    await asyncio.sleep(0.5)

        return all_jobs

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize an Adzuna job entry."""
        title = raw_job.get("title", "").strip()
        company = (raw_job.get("company", {}) or {}).get("display_name", "").strip()
        description = raw_job.get("description", "")
        url = raw_job.get("redirect_url", "")

        if not title or not url:
            return None

        company = company or "Unknown"
        description_clean = clean_html(description) if description else title

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

        location = (raw_job.get("location", {}) or {}).get("display_name", "Remote")
        tags = extract_tags(f"{title} {description_clean}")

        posted_at = None
        created = raw_job.get("created")
        if created:
            try:
                posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        country = raw_job.get("_country", "us")
        currency_map = {"us": "USD", "gb": "GBP", "ca": "CAD", "de": "EUR"}

        return {
            "title": title,
            "company": company,
            "location": location or "Remote",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": currency_map.get(country, "USD"),
            "description": description_clean,
            "requirements": None,
            "url": url,
            "posted_at": posted_at,
            "tags": tags,
        }
