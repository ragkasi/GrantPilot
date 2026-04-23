"""CRUD operations for Organization — backed by SQLAlchemy session."""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


def _org_id() -> str:
    return f"org_{uuid.uuid4().hex[:12]}"


def create_organization(db: Session, data: OrganizationCreate) -> Organization:
    org = Organization(
        id=_org_id(),
        name=data.name,
        mission=data.mission,
        location=data.location,
        nonprofit_type=data.nonprofit_type,
        annual_budget=data.annual_budget,
        population_served=data.population_served,
    )
    db.add(org)
    db.flush()  # assign DB defaults; caller commits
    return org


def get_organization(db: Session, org_id: str) -> Organization | None:
    return db.get(Organization, org_id)


def list_organizations(db: Session) -> list[Organization]:
    return db.query(Organization).all()
