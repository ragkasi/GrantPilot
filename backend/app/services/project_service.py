"""CRUD operations for Project — backed by SQLAlchemy session."""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate


def _proj_id() -> str:
    return f"proj_{uuid.uuid4().hex[:12]}"


def create_project(db: Session, data: ProjectCreate) -> Project:
    project = Project(
        id=_proj_id(),
        organization_id=data.organization_id,
        grant_name=data.grant_name,
        grant_source_url=data.grant_source_url,
        funder_name=data.funder_name,
        grant_amount=data.grant_amount,
        deadline=data.deadline,
    )
    db.add(project)
    db.flush()
    return project


def get_project(db: Session, project_id: str) -> Project | None:
    return db.get(Project, project_id)


def list_projects_for_org(db: Session, org_id: str) -> list[Project]:
    return db.query(Project).filter(Project.organization_id == org_id).all()


def list_projects_for_user(db: Session, user_id: str) -> list[Project]:
    """All projects across all organizations owned by the user."""
    from app.models.organization import Organization
    return (
        db.query(Project)
        .join(Organization, Project.organization_id == Organization.id)
        .filter(Organization.user_id == user_id)
        .order_by(Project.created_at.desc())
        .all()
    )


def update_project(db: Session, project_id: str, data) -> Project | None:
    """Partial update — only fields explicitly set in the request are applied."""
    project = db.get(Project, project_id)
    if project is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    project.updated_at = datetime.now(timezone.utc)
    db.flush()
    return project


def update_project_status(db: Session, project_id: str, status: str) -> Project | None:
    project = db.get(Project, project_id)
    if project is None:
        return None
    project.status = status
    project.updated_at = datetime.now(timezone.utc)
    db.flush()
    return project
