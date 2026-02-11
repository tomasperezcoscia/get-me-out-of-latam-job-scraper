"""SQLAlchemy 2.0 ORM models with pgvector support."""

import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# --- Enums ---


class JobStatus(str, enum.Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    RESPONDED = "responded"
    INTERVIEWING = "interviewing"
    TECHNICAL_TEST = "technical_test"
    OFFER = "offer"
    REJECTED = "rejected"


class VettingStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"


# --- Models ---


class Job(Base):
    """A job listing collected from any data source."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), index=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    embedding = mapped_column(Vector(768), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Float, index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        default=JobStatus.NEW,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    applications: Mapped[list["Application"]] = relationship(back_populates="job")

    def __repr__(self) -> str:
        return f"<Job {self.title!r} @ {self.company!r}>"


class Application(Base):
    """A job application submitted by the user."""

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)
    resume_version: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.APPLIED,
    )
    follow_up_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interview_notes: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job: Mapped["Job"] = relationship(back_populates="applications")

    def __repr__(self) -> str:
        return f"<Application job={self.job_id} status={self.status.value}>"


class PremiumPlatform(Base):
    """Tracking for premium job platform applications (Toptal, Turing, etc.)."""

    __tablename__ = "premium_platforms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    vetting_status: Mapped[VettingStatus] = mapped_column(
        Enum(VettingStatus, name="vetting_status"),
        default=VettingStatus.PENDING,
    )
    profile_url: Mapped[str | None] = mapped_column(String(500))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    test_score: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PremiumPlatform {self.platform!r} status={self.vetting_status.value}>"


class UserProfile(Base):
    """Singleton user profile for job matching and application generation."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    primary_skills: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    desired_salary_min: Mapped[int | None] = mapped_column(Integer)
    desired_salary_max: Mapped[int | None] = mapped_column(Integer)
    base_resume_path: Mapped[str | None] = mapped_column(String(500))
    base_cover_letter: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    bio: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserProfile {self.full_name!r}>"


class LearningItem(Base):
    """A skill gap item identified by AI for a specific job application."""

    __tablename__ = "learning_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    detail: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_known: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job: Mapped["Job"] = relationship()

    def __repr__(self) -> str:
        return f"<LearningItem {self.skill!r}: {self.detail!r}>"
