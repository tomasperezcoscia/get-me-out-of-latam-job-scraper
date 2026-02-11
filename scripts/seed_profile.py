"""Seed the database with the user profile."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import UserProfile


def seed_profile(force: bool = False) -> None:
    """Create or update the singleton user profile."""
    db = SessionLocal()
    try:
        existing = db.query(UserProfile).first()
        if existing and not force:
            print(f"Profile already exists: {existing.full_name}")
            print("Use --force to overwrite.")
            return

        if existing and force:
            db.delete(existing)
            db.flush()
            print("Deleted existing profile.")

        profile = UserProfile(
            full_name="Tomás Pérez Coscia",
            email="perezcosciatomas@gmail.com",
            phone="",
            location="Olavarría, Buenos Aires, Argentina",
            timezone="America/Argentina/Buenos_Aires",
            linkedin_url="https://www.linkedin.com/in/tomas-perez-coscia",
            github_url="https://github.com/tomasperezcoscia",
            portfolio_url="",
            primary_skills=[
                "Ruby on Rails",
                "Go",
                "React",
                "Smalltalk",
                "Python",
                "PostgreSQL",
                "Node.js",
                "JavaScript",
                "SQL",
                "REST APIs",
            ],
            years_experience=4,
            desired_salary_min=50000,
            desired_salary_max=80000,
            base_resume_path="Tomas_Perez_Coscia_Backend_Engineer_CV.docx",
            base_cover_letter="",
            languages=["Spanish (native)", "English (C2 Proficient)"],
            bio=(
                "Backend Software Engineer with 4+ years of experience building "
                "production systems, APIs, and full-stack applications. Strong foundation "
                "in database optimization, system architecture, and technical analysis. "
                "Currently expanding expertise in Go and systems programming. "
                "Experienced with Ruby on Rails, Smalltalk, React, Python, Node.js, and "
                "relational databases (PostgreSQL, SQL Server). "
                "Based in Argentina, available for remote work in US/EU timezones. "
                "Computer Systems Analysis background from UNICEN."
            ),
        )

        db.add(profile)
        db.commit()
        print(f"Profile seeded: {profile.full_name}")
        print(f"Skills: {', '.join(profile.primary_skills)}")
        print(f"Salary range: ${profile.desired_salary_min:,}-${profile.desired_salary_max:,} USD")
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed_profile(force=force)
