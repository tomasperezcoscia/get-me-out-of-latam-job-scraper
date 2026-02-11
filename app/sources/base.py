"""Base class for all job data sources."""

import abc
from datetime import datetime, timezone

import httpx
import structlog
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import Job

logger = structlog.get_logger(__name__)

USER_AGENT = "JobHunterPro/0.1 (personal job search automation; contact: tomas@example.com)"
DEFAULT_TIMEOUT = 30.0


class BaseSource(abc.ABC):
    """Abstract base class for job data sources.

    Subclasses must implement:
        - source_name: str property identifying this source
        - fetch(): collect raw job data from the API/feed
        - normalize(raw): convert a raw job dict to Job-compatible fields
    """

    @property
    @abc.abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source (e.g. 'remoteok', 'himalayas')."""
        ...

    @abc.abstractmethod
    async def fetch(self) -> list[dict]:
        """Fetch raw job listings from the source.

        Returns:
            List of raw job dicts as returned by the API/feed.
        """
        ...

    @abc.abstractmethod
    def normalize(self, raw_job: dict) -> dict | None:
        """Normalize a raw job dict into Job model fields.

        Returns:
            Dict with keys matching Job model columns, or None to skip.
        """
        ...

    def _get_client(self, **kwargs) -> httpx.AsyncClient:
        """Create an httpx async client with standard headers."""
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", USER_AGENT)
        headers.setdefault("Accept", "application/json")
        return httpx.AsyncClient(
            headers=headers,
            timeout=kwargs.pop("timeout", DEFAULT_TIMEOUT),
            follow_redirects=True,
            **kwargs,
        )

    async def collect(self) -> list[dict]:
        """Fetch and normalize all jobs from this source.

        Returns:
            List of normalized job dicts ready for DB insertion.
        """
        logger.info("source.fetch.start", source=self.source_name)

        try:
            raw_jobs = await self.fetch()
        except Exception:
            logger.exception("source.fetch.error", source=self.source_name)
            return []

        logger.info("source.fetch.done", source=self.source_name, raw_count=len(raw_jobs))

        normalized = []
        for raw in raw_jobs:
            try:
                job_data = self.normalize(raw)
                if job_data:
                    job_data["source"] = self.source_name
                    job_data.setdefault("scraped_at", datetime.now(timezone.utc))
                    job_data.setdefault("is_remote", True)
                    job_data.setdefault("status", "new")
                    normalized.append(job_data)
            except Exception:
                logger.exception(
                    "source.normalize.error",
                    source=self.source_name,
                    raw_job_keys=list(raw.keys()) if isinstance(raw, dict) else "N/A",
                )

        logger.info(
            "source.normalize.done",
            source=self.source_name,
            normalized_count=len(normalized),
            skipped=len(raw_jobs) - len(normalized),
        )
        return normalized

    def save(self, jobs: list[dict], db: Session) -> int:
        """Save normalized jobs to the database with upsert (skip duplicates by URL).

        Returns:
            Number of new jobs inserted.
        """
        if not jobs:
            return 0

        inserted = 0
        for job_data in jobs:
            stmt = (
                pg_insert(Job)
                .values(**job_data)
                .on_conflict_do_nothing(index_elements=["url"])
            )
            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1

        db.commit()
        logger.info(
            "source.save.done",
            source=self.source_name,
            inserted=inserted,
            duplicates=len(jobs) - inserted,
        )
        return inserted
