"""We Work Remotely data source — Tier 1 RSS feeds."""

import asyncio
from datetime import datetime, timezone

import feedparser
import httpx
import structlog

from app.sources.base import BaseSource, USER_AGENT
from app.utils.parsers import clean_html, extract_tags

logger = structlog.get_logger(__name__)

RSS_FEEDS = [
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]


class WeWorkRemotelySource(BaseSource):
    """Fetch jobs from We Work Remotely RSS feeds."""

    @property
    def source_name(self) -> str:
        return "weworkremotely"

    async def fetch(self) -> list[dict]:
        """Fetch and parse all RSS feeds."""
        all_entries = []
        seen_links = set()

        async with self._get_client() as client:
            for feed_url in RSS_FEEDS:
                try:
                    resp = await client.get(
                        feed_url,
                        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml"},
                    )
                    resp.raise_for_status()

                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        link = entry.get("link", "")
                        if link and link not in seen_links:
                            seen_links.add(link)
                            all_entries.append(entry)

                except Exception:
                    logger.exception("wwr.feed.error", feed_url=feed_url)

                await asyncio.sleep(1)

        return all_entries

    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize an RSS feed entry.

        WWR titles are typically 'Company: Job Title' format.
        """
        raw_title = raw_job.get("title", "").strip()
        url = raw_job.get("link", "")
        description = raw_job.get("summary", "") or raw_job.get("description", "")

        if not raw_title or not url:
            return None

        # Parse "Company: Job Title" format
        if ": " in raw_title:
            company, title = raw_title.split(": ", 1)
        else:
            title = raw_title
            company = "Unknown"

        title = title.strip()
        company = company.strip()

        if not title:
            return None

        description_clean = clean_html(description)
        if not description_clean:
            return None

        # Tags
        tags = extract_tags(f"{title} {description_clean}")

        # Date
        posted_at = None
        published = raw_job.get("published_parsed") or raw_job.get("updated_parsed")
        if published:
            try:
                posted_at = datetime(*published[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        return {
            "title": title,
            "company": company,
            "location": "Remote",
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "USD",
            "description": description_clean,
            "requirements": None,
            "url": url,
            "posted_at": posted_at,
            "tags": tags,
        }
