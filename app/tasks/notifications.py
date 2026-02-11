"""Celery tasks for notifications (email digest, telegram alerts)."""

import smtplib
from email.mime.text import MIMEText

import structlog
from sqlalchemy import desc

from app.config import get_settings
from app.database import SessionLocal
from app.models import Job, JobStatus
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _build_digest_html(jobs: list[Job]) -> str:
    """Build HTML email body for daily digest."""
    lines = ["<h2>JobHunter Pro — Daily Digest</h2>"]
    lines.append(f"<p>Top {len(jobs)} new matches today:</p><ol>")

    for job in jobs:
        salary = ""
        if job.salary_min:
            smax = f"-${job.salary_max:,}" if job.salary_max else "+"
            salary = f" | ${job.salary_min:,}{smax}"

        score = f"[{job.match_score:.0f}] " if job.match_score else ""
        lines.append(
            f'<li><strong>{score}<a href="{job.url}">{job.title}</a></strong>'
            f" @ {job.company}{salary}<br>"
            f"<small>{job.source} | {', '.join((job.tags or [])[:5])}</small></li>"
        )

    lines.append("</ol>")
    return "\n".join(lines)


@celery_app.task(name="app.tasks.notifications.daily_digest")
def daily_digest() -> dict:
    """Send daily email digest with top 10 new matches (score > 70)."""
    settings = get_settings()
    if not settings.smtp_user or not settings.notification_email:
        logger.warning("notifications.no_email_config")
        return {"sent": False, "reason": "Email not configured"}

    db = SessionLocal()
    try:
        top_jobs = (
            db.query(Job)
            .filter(Job.status == JobStatus.NEW)
            .filter(Job.match_score >= 70)
            .order_by(desc(Job.match_score))
            .limit(10)
            .all()
        )

        if not top_jobs:
            logger.info("notifications.no_matches")
            return {"sent": False, "reason": "No high-scoring matches"}

        html = _build_digest_html(top_jobs)

        msg = MIMEText(html, "html")
        msg["Subject"] = f"JobHunter: {len(top_jobs)} new matches (top: {top_jobs[0].match_score:.0f})"
        msg["From"] = settings.smtp_user
        msg["To"] = settings.notification_email

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("notifications.digest_sent", count=len(top_jobs))
        return {"sent": True, "jobs_count": len(top_jobs)}

    finally:
        db.close()


@celery_app.task(name="app.tasks.notifications.telegram_alert")
def telegram_alert(job_id: str) -> dict:
    """Send a Telegram alert for a high-scoring job."""
    import httpx

    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return {"sent": False, "reason": "Telegram not configured"}

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"sent": False, "reason": "Job not found"}

        score = f"Score: {job.match_score:.0f}" if job.match_score else "Unscored"
        salary = ""
        if job.salary_min:
            salary = f"\nSalary: ${job.salary_min:,}+"

        message = (
            f"🎯 *New High Match!*\n\n"
            f"*{job.title}* @ {job.company}\n"
            f"{score}{salary}\n"
            f"Source: {job.source}\n\n"
            f"[Apply]({job.url})"
        )

        resp = httpx.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={
                "chat_id": settings.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
        )
        resp.raise_for_status()
        return {"sent": True}

    finally:
        db.close()
