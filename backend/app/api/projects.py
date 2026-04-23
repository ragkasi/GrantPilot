from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectSummary
from app.services import organization_service, project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectSummary, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectSummary:
    if organization_service.get_organization(db, body.organization_id) is None:
        raise HTTPException(status_code=404, detail="Organization not found.")
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
) -> ProjectResponse:
    record = project_service.get_project(db, project_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Project not found.")
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
