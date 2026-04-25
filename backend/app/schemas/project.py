from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

ProjectStatus = Literal[
    "draft",
    "documents_uploaded",
    "analyzing",
    "analyzed",
    "report_generated",
    "error",
]


class ProjectCreate(BaseModel):
    organization_id: str
    grant_name: str = Field(..., min_length=1, max_length=300)
    grant_source_url: str | None = None
    funder_name: str | None = None
    grant_amount: str | None = None
    deadline: str | None = None


class ProjectUpdate(BaseModel):
    """Partial update — only fields that are explicitly included will be changed."""
    grant_name: str | None = Field(None, min_length=1, max_length=300)
    funder_name: str | None = None
    grant_amount: str | None = None
    deadline: str | None = None
    grant_source_url: str | None = None


class ProjectResponse(BaseModel):
    id: str
    organization_id: str
    grant_name: str
    grant_source_url: str | None
    funder_name: str | None
    grant_amount: str | None
    deadline: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectSummary(BaseModel):
    """Lightweight response used when creating a project."""
    id: str
    organization_id: str
    grant_name: str
    status: ProjectStatus
