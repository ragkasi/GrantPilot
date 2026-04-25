from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_org_access, require_project_access
from app.core.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectSummary, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_response(r) -> ProjectResponse:
    return ProjectResponse(
        id=r.id,
        organization_id=r.organization_id,
        grant_name=r.grant_name,
        grant_source_url=r.grant_source_url,
        funder_name=r.funder_name,
        grant_amount=r.grant_amount,
        deadline=r.deadline,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    records = project_service.list_projects_for_user(db, current_user.id)
    return [_to_response(r) for r in records]


@router.post("", response_model=ProjectSummary, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectSummary:
    require_org_access(db, body.organization_id, current_user)
    record = project_service.create_project(db, body)
    return ProjectSummary(
        id=record.id,
        organization_id=record.organization_id,
        grant_name=record.grant_name,
        status=record.status,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    record = require_project_access(db, project_id, current_user)
    return _to_response(record)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    """Partial update — only provided fields are changed. Status is not editable here."""
    require_project_access(db, project_id, current_user)
    updated = project_service.update_project(db, project_id, body)
    return _to_response(updated)
