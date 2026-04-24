"""
Demo seed — populates the BrightPath demo org, project, and analysis on startup.

Uses stable IDs matching the frontend demo links so the demo flow works
without any manual API calls. Idempotent: safe to call multiple times.
"""
from sqlalchemy.orm import Session

from app.models.analysis import ReadinessReport
from app.models.organization import Organization
from app.models.project import Project
from app.services import analysis_service

DEMO_ORG_ID = "org_brightpath"
DEMO_PROJECT_ID = "proj_stem_2026"


def seed_demo(db: Session) -> None:
    if db.get(Organization, DEMO_ORG_ID) is not None:
        # DB already has demo data — ensure ReadinessReport exists (e.g. after schema upgrades).
        existing_report = (
            db.query(ReadinessReport)
            .filter(ReadinessReport.project_id == DEMO_PROJECT_ID)
            .first()
        )
        if existing_report is None:
            analysis_service.run_analysis(DEMO_PROJECT_ID, db)
        return

    org = Organization(
        id=DEMO_ORG_ID,
        name="BrightPath Youth Foundation",
        mission=(
            "Provide after-school STEM mentoring and academic support to low-income "
            "middle school students in Columbus, Ohio."
        ),
        location="Columbus, Ohio",
        nonprofit_type="501(c)(3)",
        annual_budget=420_000,
        population_served="Low-income middle school students (grades 6–8)",
    )
    db.add(org)

    project = Project(
        id=DEMO_PROJECT_ID,
        organization_id=DEMO_ORG_ID,
        grant_name="Community STEM Access Fund",
        grant_source_url=None,
        funder_name="Ohio Community Foundation",
        grant_amount="$50,000 – $150,000",
        deadline="May 15, 2026",
        status="analyzed",
    )
    db.add(project)
    db.flush()

    # Persist mock analysis results to ReadinessReport so GET /analysis works immediately.
    analysis_service.run_analysis(DEMO_PROJECT_ID, db)
