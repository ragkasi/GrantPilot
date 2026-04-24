from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_org_access
from app.core.database import get_db
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationSummary
from app.services import organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


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
