from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_org_access, require_project_access
from app.core.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectSummary
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectSummary, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectSummary:
    # Verify org ownership before creating the project under it
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
    return ProjectResponse(
        id=record.id,
        organization_id=record.organization_id,
        grant_name=record.grant_name,
        grant_source_url=record.grant_source_url,
        funder_name=record.funder_name,
        grant_amount=record.grant_amount,
        deadline=record.deadline,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
