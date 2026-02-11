"""Initialize the database: create all tables from ORM models."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database import engine
from app.models import Base


def init_db() -> None:
    """Create all tables and enable pgvector extension."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")
    print("Tables created:")
    for table_name in Base.metadata.tables:
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_db()
