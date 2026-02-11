"""SerpAPI Google Jobs — Tier 2 paid API ($75/mo)."""

import asyncio

import structlog

from app.config import get_settings
from app.sources.base import BaseSource
from app.utils.parsers import clean_html, extract_tags, parse_salary

logger = structlog.get_logger(__name__)

API_URL = "https://serpapi.com/search"
QUERIES = [
    "remote python developer",
    "remote ruby on rails developer",
    "remote golang developer",
    "remote fullstack developer",
    "remote react developer",
]


class SerpAPIGoogleSource(BaseSource):
    """Fetch jobs from Google Jobs via SerpAPI."""

    @property
    def source_name(self) -> str:
        return "serpapi_google"

    async def fetch(self) -> list[dict]:
        """Search Google Jobs via SerpAPI for multiple queries."""
        settings = get_settings()
        if not settings.serpapi_key:
            logger.warning("serpapi.no_key", msg="SERPAPI_KEY not set, skipping")
            return []

        all_jobs = []
        seen_titles = set()

        async with self._get_client() as client:
            for query in QUERIES:
                try:
                    resp = await client.get(
                        API_URL,
                        params={
                            "engine": "google_jobs",
                            "q": query,
                            "api_key": settings.serpapi_key,
                            "hl": "en",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for job in data.get("jobs_results", []):
                        key = f"{job.get('title', '')}-{job.get('company_name', '')}"
                        if key not in seen_titles:
                            seen_titles.add(key)
                            all_jobs.append(job)

                except Exception:
                    logger.exception("serpapi.search.error", query=query)

                await asyncio.sleep(1)

        return all_jobs

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize a SerpAPI Google Jobs result."""
        title = raw_job.get("title", "").strip()
        company = raw_job.get("company_name", "").strip()
        description = raw_job.get("description", "")
        location = raw_job.get("location", "Remote")

        if not title or not company:
            return None

        description_clean = clean_html(description) if description else title

        # SerpAPI provides salary in detected_extensions
        extensions = raw_job.get("detected_extensions", {})
        salary_text = extensions.get("salary", "")
        salary_min, salary_max, currency = parse_salary(salary_text)

        # Build a URL from related links or use a search-based fallback
        related = raw_job.get("related_links", [])
        url = ""
        for link in related:
            if link.get("link"):
                url = link["link"]
                break

        if not url:
            # Use job_id-based apply link if available
            apply_options = raw_job.get("apply_options", [])
            for opt in apply_options:
                if opt.get("link"):
                    url = opt["link"]
                    break

        if not url:
            return None

        tags = extract_tags(f"{title} {description_clean}")

        return {
            "title": title,
            "company": company,
            "location": location,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": currency,
            "description": description_clean,
            "requirements": None,
            "url": url,
            "posted_at": None,
            "tags": tags,
        }
