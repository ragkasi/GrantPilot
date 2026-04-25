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


def delete_project(db: Session, project_id: str) -> bool:
    """Delete a project and all its associated data.

    Cascade order:
      EvidenceMatch → GrantRequirement → ReadinessReport
      DocumentChunk + files → Document
      Project

    Returns True if found and deleted, False if not found.
    """
    from app.models.analysis import EvidenceMatch, GrantRequirement, ReadinessReport
    from app.models.chunk import DocumentChunk
    from app.models.document import Document
    from app.services import storage_service
    import logging

    logger = logging.getLogger(__name__)

    project = db.get(Project, project_id)
    if project is None:
        return False

    # Collect requirement IDs so we can delete their evidence matches
    req_ids: list[str] = [
        r.id for r in db.query(GrantRequirement)
        .filter(GrantRequirement.project_id == project_id)
        .all()
    ]

    # EvidenceMatch → GrantRequirement
    if req_ids:
        db.query(EvidenceMatch).filter(
            EvidenceMatch.requirement_id.in_(req_ids)
        ).delete(synchronize_session="fetch")

    db.query(GrantRequirement).filter(
        GrantRequirement.project_id == project_id
    ).delete(synchronize_session="fetch")

    # ReadinessReport
    db.query(ReadinessReport).filter(
        ReadinessReport.project_id == project_id
    ).delete(synchronize_session="fetch")

    # DocumentChunk + file + Document
    docs = db.query(Document).filter(Document.project_id == project_id).all()
    for doc in docs:
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).delete(synchronize_session="fetch")
        if doc.storage_url:
            try:
                path = storage_service.get_file_path(doc.storage_url)
                if path.exists():
                    path.unlink()
            except Exception as exc:
                logger.warning("Could not remove file %s: %s", doc.storage_url, exc)
        db.delete(doc)

    db.delete(project)
    db.flush()
    return True


def update_project_status(db: Session, project_id: str, status: str) -> Project | None:
    project = db.get(Project, project_id)
    if project is None:
        return None
    project.status = status
    project.updated_at = datetime.now(timezone.utc)
    db.flush()
    return project
