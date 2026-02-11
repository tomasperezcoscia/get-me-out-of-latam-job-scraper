"""Pydantic request/response schemas for the API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobOut(BaseModel):
    """Job listing response schema."""

    id: UUID
    title: str
    company: str
    location: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    description: str
    requirements: str | None
    url: str
    source: str | None
    posted_at: datetime | None
    scraped_at: datetime
    is_remote: bool
    tags: list[str] | None
    match_score: float | None
    status: str
    notes: str | None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Paginated job list response."""

    items: list[JobOut]
    total: int
    skip: int
    limit: int


class JobStatusUpdate(BaseModel):
    """Update job status."""

    status: str
    notes: str | None = None


class StatsOut(BaseModel):
    """Collection statistics response."""

    total_jobs: int
    by_source: dict[str, int]
    by_status: dict[str, int]
    jobs_with_salary: int
    avg_salary_min: float | None
    avg_salary_max: float | None


class ProfileOut(BaseModel):
    """User profile response."""

    id: UUID
    full_name: str
    email: str | None
    location: str | None
    timezone: str | None
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    primary_skills: list[str] | None
    years_experience: int | None
    desired_salary_min: int | None
    desired_salary_max: int | None
    languages: list[str] | None
    bio: str | None

    model_config = {"from_attributes": True}


class CollectResult(BaseModel):
    """Result of a collection run."""

    source: str
    fetched: int
    inserted: int


class ApplicationCreate(BaseModel):
    """Create a new application."""

    job_id: UUID
    cover_letter: str | None = None
    resume_version: str | None = None


class ApplicationOut(BaseModel):
    """Application response schema."""

    id: UUID
    job_id: UUID
    applied_at: datetime
    cover_letter: str | None
    resume_version: str | None
    status: str
    follow_up_date: datetime | None
    interview_notes: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationUpdate(BaseModel):
    """Update an application."""

    status: str | None = None
    notes: str | None = None
    interview_notes: str | None = None
    follow_up_date: datetime | None = None


class ApplicationWithJobOut(BaseModel):
    """Application response with job info for pipeline views."""

    id: UUID
    job_id: UUID
    job_title: str
    job_company: str
    job_url: str
    job_score: float | None
    applied_at: datetime
    cover_letter: str | None
    resume_version: str | None
    status: str
    follow_up_date: datetime | None
    interview_notes: str | None
    notes: str | None
    created_at: datetime


class ATSCheckRequest(BaseModel):
    """Request body for ATS compatibility check."""

    resume_text: str


# --- Mass Apply ---


class MassApplyRequest(BaseModel):
    """Request body for mass apply."""

    job_ids: list[UUID]


class MassApplyStarted(BaseModel):
    """Response after kicking off mass apply."""

    task_id: str
    total: int


class MassApplyProgress(BaseModel):
    """Progress of a running mass apply task."""

    task_id: str
    total: int
    completed: int
    failed: int
    current_job: str | None
    results: list[dict]
    done: bool


# --- Learning Items ---


class LearningItemOut(BaseModel):
    """Learning item response schema."""

    id: UUID
    job_id: UUID
    skill: str
    detail: str
    category: str
    is_known: bool

    model_config = {"from_attributes": True}


class LearningItemUpdate(BaseModel):
    """Update a learning item."""

    is_known: bool


class SkillSummary(BaseModel):
    """Aggregated skill across all jobs for the profile learning dashboard."""

    skill: str
    category: str
    job_count: int
    is_known: bool
    details: list[str]
