"""Test an individual data source.

Usage:
    python scripts/test_source.py remoteok          # fetch + display, don't save
    python scripts/test_source.py remoteok --save    # fetch + save to DB
    python scripts/test_source.py --list             # list available sources
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.sources import SOURCE_REGISTRY, get_source
from app.utils.logger import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Test a job data source")
    parser.add_argument("source", nargs="?", help="Source name to test")
    parser.add_argument("--save", action="store_true", help="Save fetched jobs to DB")
    parser.add_argument("--list", action="store_true", help="List available sources")
    args = parser.parse_args()

    setup_logging("INFO")

    if args.list:
        print("Available sources:")
        for name in SOURCE_REGISTRY:
            print(f"  - {name}")
        return

    if not args.source:
        parser.print_help()
        return

    source = get_source(args.source)
    print(f"\n--- Testing source: {source.source_name} ---\n")

    # Fetch and normalize
    jobs = asyncio.run(source.collect())

    print(f"\nNormalized jobs: {len(jobs)}\n")

    # Display sample
    for i, job in enumerate(jobs[:5]):
        print(f"  [{i+1}] {job['title']}")
        print(f"      Company:  {job['company']}")
        print(f"      Location: {job['location']}")
        salary = ""
        if job.get("salary_min") or job.get("salary_max"):
            smin = f"${job['salary_min']:,}" if job.get("salary_min") else "?"
            smax = f"${job['salary_max']:,}" if job.get("salary_max") else "?"
            salary = f"{smin} - {smax} {job.get('salary_currency', 'USD')}"
        print(f"      Salary:   {salary or 'Not specified'}")
        print(f"      Tags:     {', '.join(job.get('tags', [])[:8])}")
        print(f"      URL:      {job['url'][:80]}")
        print()

    if len(jobs) > 5:
        print(f"  ... and {len(jobs) - 5} more\n")

    # Save if requested
    if args.save and jobs:
        db = SessionLocal()
        try:
            inserted = source.save(jobs, db)
            print(f"Saved: {inserted} new jobs ({len(jobs) - inserted} duplicates)")
        finally:
            db.close()
    elif not args.save and jobs:
        print("(Use --save to persist to database)")


if __name__ == "__main__":
    main()
