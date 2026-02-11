"""Data source trigger routes."""

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import CollectResult
from app.database import get_db
from app.sources import SOURCE_REGISTRY, get_all_sources, get_source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/")
def list_sources() -> list[str]:
    """List available data sources."""
    return list(SOURCE_REGISTRY.keys())


@router.post("/collect/{source_name}", response_model=CollectResult)
def collect_source(source_name: str, db: Session = Depends(get_db)) -> dict:
    """Trigger collection from a specific source."""
    source = get_source(source_name)
    jobs = asyncio.run(source.collect())
    inserted = source.save(jobs, db) if jobs else 0

    return {"source": source_name, "fetched": len(jobs), "inserted": inserted}


@router.post("/collect-all", response_model=list[CollectResult])
def collect_all(db: Session = Depends(get_db)) -> list[dict]:
    """Trigger collection from all sources."""
    results = []
    for source in get_all_sources():
        try:
            jobs = asyncio.run(source.collect())
            inserted = source.save(jobs, db) if jobs else 0
            results.append({
                "source": source.source_name,
                "fetched": len(jobs),
                "inserted": inserted,
            })
        except Exception:
            results.append({
                "source": source.source_name,
                "fetched": 0,
                "inserted": 0,
            })
    return results
