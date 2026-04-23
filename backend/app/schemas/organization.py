from datetime import datetime
from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    mission: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    nonprofit_type: str = Field(..., min_length=1)
    annual_budget: float = Field(..., ge=0)
    population_served: str = Field(..., min_length=1)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    mission: str
    location: str
    nonprofit_type: str
    annual_budget: float
    population_served: str
    created_at: datetime
    updated_at: datetime


class OrganizationSummary(BaseModel):
    """Lightweight response used when creating an organization."""
    id: str
    name: str
    created_at: datetime
