from datetime import datetime
from typing import Literal
from pydantic import BaseModel

DocumentType = Literal[
    "mission_statement",
    "budget",
    "annual_report",
    "program_description",
    "irs_letter",
    "past_application",
    "grant_opportunity",
    "other",
]


class DocumentResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    filename: str
    document_type: DocumentType
    status: str
    page_count: int | None
    created_at: datetime


class DocumentSummary(BaseModel):
    """Lightweight response returned immediately after upload."""
    id: str
    filename: str
    document_type: DocumentType
    status: str
