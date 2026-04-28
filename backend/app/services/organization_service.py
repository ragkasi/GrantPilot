"""CRUD operations for Organization — backed by SQLAlchemy session."""
import uuid

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


def _org_id() -> str:
    return f"org_{uuid.uuid4().hex[:12]}"


def create_organization(
    db: Session, data: OrganizationCreate, user_id: str | None = None
) -> Organization:
    org = Organization(
        id=_org_id(),
        user_id=user_id,
        name=data.name,
        mission=data.mission,
        location=data.location,
        nonprofit_type=data.nonprofit_type,
        annual_budget=data.annual_budget,
        population_served=data.population_served,
    )
    db.add(org)
    db.flush()
    return org


def get_organization(db: Session, org_id: str) -> Organization | None:
    return db.get(Organization, org_id)


def list_organizations_for_user(db: Session, user_id: str) -> list[Organization]:
    return db.query(Organization).filter(Organization.user_id == user_id).all()


def list_organizations(db: Session) -> list[Organization]:
    return db.query(Organization).all()


def delete_organization(db: Session, org_id: str) -> bool:
    """Delete an organization and all its projects (cascading through analysis/docs/chunks).

    Returns True if found and deleted, False if not found.
    Deletion order: projects (each via project_service.delete_project) → organization.
    """
    from app.models.project import Project
    from app.services.project_service import delete_project

    org = db.get(Organization, org_id)
    if org is None:
        return False

    project_ids = [
        p.id for p in db.query(Project).filter(Project.organization_id == org_id).all()
    ]
    for pid in project_ids:
        delete_project(db, pid)

    db.delete(org)
    db.flush()
    return True
