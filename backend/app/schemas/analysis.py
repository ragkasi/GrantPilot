from typing import Literal
from pydantic import BaseModel, Field

RequirementType = Literal[
    "eligibility",
    "required_document",
    "budget",
    "narrative",
    "impact",
    "geography",
    "population",
    "compliance",
    "deadline",
]

RequirementImportance = Literal["required", "preferred", "optional", "unknown"]

RequirementStatus = Literal["satisfied", "partially_satisfied", "not_satisfied", "unclear"]

RiskSeverity = Literal["high", "medium", "low"]


class Citation(BaseModel):
    document_name: str
    page_number: int
    summary: str


class RequirementResult(BaseModel):
    id: str
    text: str
    type: RequirementType
    importance: RequirementImportance
    status: RequirementStatus
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[Citation]


class MissingDocument(BaseModel):
    name: str
    required: bool
    description: str


class RiskFlag(BaseModel):
    severity: RiskSeverity
    title: str
    description: str


class DraftAnswer(BaseModel):
    id: str
    question: str
    draft_answer: str
    citations: list[Citation]
    missing_evidence: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


class AnalysisResponse(BaseModel):
    project_id: str
    eligibility_score: int = Field(..., ge=0, le=100)
    readiness_score: int = Field(..., ge=0, le=100)
    requirements: list[RequirementResult]
    missing_documents: list[MissingDocument]
    risk_flags: list[RiskFlag]
    draft_answers: list[DraftAnswer]


class AnalyzeResponse(BaseModel):
    """Returned immediately when analysis is triggered."""
    project_id: str
    status: str


class ReportResponse(BaseModel):
    project_id: str
    report_pdf_url: str | None
