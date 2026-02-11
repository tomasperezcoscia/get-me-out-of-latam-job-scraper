"""Shared test fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Base


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    settings = get_settings()
    eng = create_engine(settings.database_url)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    """Create a test database session."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
