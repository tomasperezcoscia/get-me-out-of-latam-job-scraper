"""Tests for ORM models."""

from app.models import Job, JobStatus, UserProfile


def test_job_creation(db):
    """Test creating a Job instance."""
    job = Job(
        title="Senior Python Developer",
        company="TestCorp",
        description="Build cool stuff with Python",
        url="https://example.com/job/1",
        source="test",
    )
    db.add(job)
    db.flush()

    assert job.id is not None
    assert job.status == JobStatus.NEW
    assert job.is_remote is True
    assert job.salary_currency == "USD"


def test_user_profile(db):
    """Test querying the user profile."""
    profile = db.query(UserProfile).first()
    assert profile is not None
    assert profile.primary_skills is not None
    assert len(profile.primary_skills) > 0
