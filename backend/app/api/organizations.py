from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_org_access
from app.core.database import get_db
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationSummary
from app.schemas.project import ProjectResponse
from app.services import organization_service, project_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationResponse]:
    """Return all organizations owned by the current user."""
    records = organization_service.list_organizations_for_user(db, current_user.id)
    return [
        OrganizationResponse(
            id=r.id,
            name=r.name,
            mission=r.mission,
            location=r.location,
            nonprofit_type=r.nonprofit_type,
            annual_budget=r.annual_budget,
            population_served=r.population_served,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.post("", response_model=OrganizationSummary, status_code=201)
def create_organization(
    body: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationSummary:
    record = organization_service.create_organization(db, body, user_id=current_user.id)
    return OrganizationSummary(id=record.id, name=record.name, created_at=record.created_at)


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationResponse:
    record = require_org_access(db, org_id, current_user)
    return OrganizationResponse(
        id=record.id,
        name=record.name,
        mission=record.mission,
        location=record.location,
        nonprofit_type=record.nonprofit_type,
        annual_budget=record.annual_budget,
        population_served=record.population_served,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/{org_id}/projects", response_model=list[ProjectResponse])
def list_org_projects(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    """Return all projects under an organization the user owns."""
    require_org_access(db, org_id, current_user)
    records = project_service.list_projects_for_org(db, org_id)
    return [
        ProjectResponse(
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
        for r in records
    ]
