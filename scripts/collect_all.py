"""Run all Tier 1 data sources and save jobs to DB.

Usage:
    python scripts/collect_all.py
    python scripts/collect_all.py --dry-run   # fetch but don't save
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.sources import get_all_sources
from app.utils.logger import setup_logging


async def collect_from_source(source) -> list[dict]:
    """Collect jobs from a single source."""
    return await source.collect()


async def run_all(dry_run: bool = False) -> None:
    setup_logging("INFO")

    sources = get_all_sources()
    print(f"Collecting from {len(sources)} sources...\n")

    total_fetched = 0
    total_inserted = 0
    results = []

    for source in sources:
        print(f"--- {source.source_name} ---")
        try:
            jobs = await source.collect()
            inserted = 0

            if jobs and not dry_run:
                db = SessionLocal()
                try:
                    inserted = source.save(jobs, db)
                finally:
                    db.close()

            total_fetched += len(jobs)
            total_inserted += inserted
            results.append((source.source_name, len(jobs), inserted))
            print(f"  Fetched: {len(jobs)}, Inserted: {inserted}\n")

        except Exception as e:
            print(f"  ERROR: {e}\n")
            results.append((source.source_name, 0, 0))

    # Summary
    print("\n" + "=" * 50)
    print("COLLECTION SUMMARY")
    print("=" * 50)
    print(f"{'Source':<20} {'Fetched':>10} {'Inserted':>10}")
    print("-" * 42)
    for name, fetched, inserted in results:
        print(f"{name:<20} {fetched:>10} {inserted:>10}")
    print("-" * 42)
    print(f"{'TOTAL':<20} {total_fetched:>10} {total_inserted:>10}")

    if dry_run:
        print("\n(Dry run — nothing was saved to DB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect jobs from all sources")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but don't save")
    args = parser.parse_args()

    asyncio.run(run_all(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
