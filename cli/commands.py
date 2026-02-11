"""JobHunter Pro CLI — daily workflow commands."""

import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import click
from sqlalchemy import func, text

# Add project root to path for direct invocation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Job, JobStatus, UserProfile
from app.sources import SOURCE_REGISTRY, get_all_sources, get_source
from app.utils.logger import setup_logging


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """JobHunter Pro — AI-powered remote job search automation."""
    setup_logging("DEBUG" if verbose else "INFO")


# --- collect ---


@cli.command()
@click.option("--source", "-s", type=click.Choice(list(SOURCE_REGISTRY.keys())), help="Specific source")
@click.option("--all", "all_sources", is_flag=True, help="Collect from all sources")
@click.option("--dry-run", is_flag=True, help="Fetch but don't save")
def collect(source: str | None, all_sources: bool, dry_run: bool) -> None:
    """Collect jobs from data sources."""
    if not source and not all_sources:
        click.echo("Specify --source NAME or --all")
        return

    sources = get_all_sources() if all_sources else [get_source(source)]

    total_fetched = 0
    total_inserted = 0

    for src in sources:
        click.echo(f"\n--- {src.source_name} ---")
        jobs = asyncio.run(src.collect())
        inserted = 0

        if jobs and not dry_run:
            db = SessionLocal()
            try:
                inserted = src.save(jobs, db)
            finally:
                db.close()

        total_fetched += len(jobs)
        total_inserted += inserted
        click.echo(f"  Fetched: {len(jobs)}, New: {inserted}")

    click.echo(f"\nTotal: {total_fetched} fetched, {total_inserted} new jobs")
    if dry_run:
        click.echo("(Dry run — nothing saved)")


# --- stats ---


@cli.command()
def stats() -> None:
    """Show job collection statistics."""
    db = SessionLocal()
    try:
        total = db.query(func.count(Job.id)).scalar()
        click.echo(f"\nTotal jobs: {total}\n")

        # By source
        click.echo("By source:")
        rows = (
            db.query(Job.source, func.count(Job.id))
            .group_by(Job.source)
            .order_by(func.count(Job.id).desc())
            .all()
        )
        for source, count in rows:
            click.echo(f"  {source:<20} {count:>6}")

        # By status
        click.echo("\nBy status:")
        rows = (
            db.query(Job.status, func.count(Job.id))
            .group_by(Job.status)
            .order_by(func.count(Job.id).desc())
            .all()
        )
        for status, count in rows:
            click.echo(f"  {status.value:<20} {count:>6}")

        # Salary stats
        with_salary = db.query(func.count(Job.id)).filter(Job.salary_min.isnot(None)).scalar()
        click.echo(f"\nJobs with salary data: {with_salary}/{total}")

        if with_salary:
            avg_min = db.query(func.avg(Job.salary_min)).filter(Job.salary_min.isnot(None)).scalar()
            avg_max = db.query(func.avg(Job.salary_max)).filter(Job.salary_max.isnot(None)).scalar()
            click.echo(f"  Avg salary range: ${avg_min:,.0f} - ${avg_max:,.0f}")

        # Top tags
        click.echo("\nTop tags:")
        tag_query = text("""
            SELECT tag, COUNT(*) as cnt
            FROM jobs, unnest(tags) AS tag
            GROUP BY tag ORDER BY cnt DESC LIMIT 15
        """)
        for row in db.execute(tag_query):
            click.echo(f"  {row[0]:<25} {row[1]:>5}")

        # Recent jobs
        click.echo("\nMost recent jobs:")
        recent = (
            db.query(Job)
            .order_by(Job.scraped_at.desc())
            .limit(5)
            .all()
        )
        for job in recent:
            salary = ""
            if job.salary_min:
                salary = f" ${job.salary_min:,}-${job.salary_max:,}" if job.salary_max else f" ${job.salary_min:,}+"
            score = f" [Score: {job.match_score:.0f}]" if job.match_score else ""
            click.echo(f"  {score}{job.title} @ {job.company}{salary}")

    finally:
        db.close()


# --- review ---


@cli.command()
@click.option("--limit", "-n", default=10, help="Number of jobs to review")
@click.option("--source", "-s", help="Filter by source")
@click.option("--min-salary", type=int, help="Minimum salary filter")
def review(limit: int, source: str | None, min_salary: int | None) -> None:
    """Interactively review new jobs."""
    db = SessionLocal()
    try:
        query = db.query(Job).filter(Job.status == JobStatus.NEW)

        if source:
            query = query.filter(Job.source == source)
        if min_salary:
            query = query.filter(
                (Job.salary_min >= min_salary) | (Job.salary_min.is_(None))
            )

        # Sort by match_score if available, then by scraped_at
        query = query.order_by(
            Job.match_score.desc().nulls_last(),
            Job.scraped_at.desc(),
        )

        jobs = query.limit(limit).all()

        if not jobs:
            click.echo("No new jobs to review!")
            return

        click.echo(f"\n{len(jobs)} jobs to review:\n")

        for i, job in enumerate(jobs, 1):
            score = f"[Score: {job.match_score:.0f}] " if job.match_score else ""
            salary = ""
            if job.salary_min:
                smax = f"-${job.salary_max:,}" if job.salary_max else "+"
                salary = f" | ${job.salary_min:,}{smax} {job.salary_currency}"

            click.echo(f"  {i}. {score}{job.title}")
            click.echo(f"     {job.company} | {job.location}{salary}")
            click.echo(f"     {job.source} | {job.url[:70]}")
            if job.tags:
                click.echo(f"     Tags: {', '.join(job.tags[:8])}")
            click.echo()

            # Interactive prompt
            action = click.prompt(
                "     Action",
                type=click.Choice(["s", "r", "a", "n", "o", "q"]),
                default="n",
                show_choices=True,
                prompt_suffix=" [s=skip, r=reviewed, a=applied, n=next, o=open, q=quit]: ",
            )

            if action == "q":
                break
            elif action == "r":
                job.status = JobStatus.REVIEWED
                db.commit()
                click.echo("     → Marked as REVIEWED")
            elif action == "a":
                job.status = JobStatus.APPLIED
                db.commit()
                click.echo("     → Marked as APPLIED")
            elif action == "s":
                job.status = JobStatus.REJECTED
                db.commit()
                click.echo("     → Skipped (REJECTED)")
            elif action == "o":
                click.launch(job.url)
                # Re-prompt after opening
                action2 = click.prompt(
                    "     After viewing",
                    type=click.Choice(["r", "a", "s", "n"]),
                    default="r",
                )
                if action2 == "r":
                    job.status = JobStatus.REVIEWED
                    db.commit()
                elif action2 == "a":
                    job.status = JobStatus.APPLIED
                    db.commit()
                elif action2 == "s":
                    job.status = JobStatus.REJECTED
                    db.commit()

    finally:
        db.close()


# --- export ---


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["csv", "json"]), default="csv")
@click.option("--status", type=click.Choice([s.value for s in JobStatus]), help="Filter by status")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
def export(fmt: str, status: str | None, output: str | None) -> None:
    """Export jobs to CSV or JSON."""
    db = SessionLocal()
    try:
        query = db.query(Job)
        if status:
            query = query.filter(Job.status == status)
        query = query.order_by(Job.match_score.desc().nulls_last(), Job.scraped_at.desc())

        jobs = query.all()

        if not jobs:
            click.echo("No jobs to export.")
            return

        fields = [
            "title", "company", "location", "salary_min", "salary_max",
            "salary_currency", "source", "status", "match_score", "url",
            "posted_at", "tags",
        ]

        rows = []
        for job in jobs:
            rows.append({
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "salary_currency": job.salary_currency,
                "source": job.source,
                "status": job.status.value,
                "match_score": job.match_score,
                "url": job.url,
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                "tags": ", ".join(job.tags) if job.tags else "",
            })

        if fmt == "json":
            content = json.dumps(rows, indent=2, default=str)
        else:
            buf = StringIO()
            writer = csv.DictWriter(buf, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
            content = buf.getvalue()

        if output:
            Path(output).write_text(content, encoding="utf-8")
            click.echo(f"Exported {len(rows)} jobs to {output}")
        else:
            click.echo(content)

    finally:
        db.close()


# --- score ---


@cli.command()
@click.option("--embed/--no-embed", default=True, help="Generate embeddings first")
@click.option("--limit", "-n", default=500, help="Max jobs to score")
def score(embed: bool, limit: int) -> None:
    """Score unscored jobs using the AI matching engine."""
    from app.ai.embeddings import embed_new_jobs
    from app.ai.matcher import score_new_jobs

    db = SessionLocal()
    try:
        if embed:
            click.echo("Generating embeddings...")
            embedded = embed_new_jobs(db, limit=limit)
            click.echo(f"  Embedded {embedded} jobs")

        click.echo("Scoring jobs...")
        scored = score_new_jobs(db, limit=limit)
        click.echo(f"  Scored {scored} jobs")

        # Show top matches
        if scored:
            top = (
                db.query(Job)
                .filter(Job.match_score.isnot(None))
                .order_by(Job.match_score.desc())
                .limit(10)
                .all()
            )
            click.echo("\nTop 10 matches:")
            for i, job in enumerate(top, 1):
                salary = ""
                if job.salary_min:
                    salary = f" ${job.salary_min:,}+"
                click.echo(
                    f"  {i:>2}. [{job.match_score:.0f}] {job.title} @ {job.company}{salary}"
                )
    finally:
        db.close()


# --- apply ---


@cli.command()
@click.argument("job_id")
@click.option("--dry-run", is_flag=True, help="Generate but don't save")
def apply(job_id: str, dry_run: bool) -> None:
    """Generate application materials for a job."""
    from app.ai.cover_letter import generate, save_cover_letter

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            click.echo(f"Job not found: {job_id}")
            return

        profile = db.query(UserProfile).first()
        if not profile:
            click.echo("No user profile found. Run: python scripts/seed_profile.py")
            return

        click.echo(f"\nJob: {job.title} @ {job.company}")
        click.echo(f"URL: {job.url}")
        click.echo()

        # Generate cover letter
        click.echo("Generating cover letter...")
        try:
            cover_letter = generate(job, profile)
            click.echo(f"\n{'=' * 60}")
            click.echo(cover_letter)
            click.echo(f"{'=' * 60}\n")

            if not dry_run:
                filepath = save_cover_letter(job, cover_letter)
                click.echo(f"Saved to: {filepath}")

                # Create application record
                from app.models import Application
                app_record = Application(job_id=job.id, cover_letter=cover_letter)
                db.add(app_record)
                job.status = JobStatus.APPLIED
                db.commit()
                click.echo(f"Status updated to APPLIED")
            else:
                click.echo("(Dry run — nothing saved)")

        except ValueError as e:
            click.echo(f"Error: {e}")
            click.echo("Set your ANTHROPIC_API_KEY in .env to generate cover letters.")

    finally:
        db.close()


if __name__ == "__main__":
    cli()
