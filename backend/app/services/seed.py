"""
Demo seed — creates demo user + BrightPath org/project/analysis on startup.

Demo credentials (for local development only):
  email:    demo@grantpilot.local
  password: DemoGrantPilot123!

Idempotent: safe to call multiple times.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.analysis import ReadinessReport
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.services import analysis_service

DEMO_EMAIL = "demo@grantpilot.local"
DEMO_PASSWORD = "DemoGrantPilot123!"
DEMO_USER_ID = "user_demo"
DEMO_ORG_ID = "org_brightpath"
DEMO_PROJECT_ID = "proj_stem_2026"


def seed_demo(db: Session) -> None:
    # 1. Ensure demo user exists
    demo_user = db.get(User, DEMO_USER_ID)
    if demo_user is None:
        demo_user = User(
            id=DEMO_USER_ID,
            email=DEMO_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            is_demo=True,
        )
        db.add(demo_user)
        db.flush()

    # 2. Ensure demo org exists and is owned by demo user
    demo_org = db.get(Organization, DEMO_ORG_ID)
    if demo_org is None:
        demo_org = Organization(
            id=DEMO_ORG_ID,
            user_id=DEMO_USER_ID,
            name="BrightPath Youth Foundation",
            mission=(
                "Provide after-school STEM mentoring and academic support to low-income "
                "middle school students in Columbus, Ohio."
            ),
            location="Columbus, Ohio",
            nonprofit_type="501(c)(3)",
            annual_budget=420_000,
            population_served="Low-income middle school students (grades 6-8)",
        )
        db.add(demo_org)
    elif demo_org.user_id is None:
        # Backfill ownership if org was seeded before auth was added
        demo_org.user_id = DEMO_USER_ID

    # 3. Ensure demo project exists
    demo_project = db.get(Project, DEMO_PROJECT_ID)
    if demo_project is None:
        demo_project = Project(
            id=DEMO_PROJECT_ID,
            organization_id=DEMO_ORG_ID,
            grant_name="Community STEM Access Fund",
            grant_source_url=None,
            funder_name="Ohio Community Foundation",
            grant_amount="$50,000 - $150,000",
            deadline="May 15, 2026",
            status="analyzed",
        )
        db.add(demo_project)

    db.flush()

    # 4. Ensure analysis exists
    if (
        db.query(ReadinessReport)
        .filter(ReadinessReport.project_id == DEMO_PROJECT_ID)
        .first()
    ) is None:
        analysis_service.run_analysis(DEMO_PROJECT_ID, db)
