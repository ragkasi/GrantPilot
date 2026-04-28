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

# Source of a completed analysis result.
AnalysisSource = Literal["real_pipeline", "fallback_mock", "seeded_demo"]


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


class AnalysisDiagnostics(BaseModel):
    """Safe, user-appropriate pipeline diagnostics — no secrets or raw prompts."""
    uploaded_doc_count: int
    parsed_doc_count: int
    chunk_count: int
    grant_opportunity_found: bool
    extracted_requirement_count: int
    embeddings_generated: bool


class AnalysisResponse(BaseModel):
    project_id: str
    eligibility_score: int = Field(..., ge=0, le=100)
    readiness_score: int = Field(..., ge=0, le=100)
    requirements: list[RequirementResult]
    missing_documents: list[MissingDocument]
    risk_flags: list[RiskFlag]
    draft_answers: list[DraftAnswer]
    # Provenance — tells the caller (and UI) how this analysis was produced.
    analysis_source: AnalysisSource | None = None
    fallback_reason: str | None = None
    diagnostics: AnalysisDiagnostics | None = None


class AnalysisSummary(BaseModel):
    """Lightweight summary for dashboard cards — avoids fetching the full payload."""
    project_id: str
    eligibility_score: int = Field(..., ge=0, le=100)
    readiness_score: int = Field(..., ge=0, le=100)
    requirement_count: int
    satisfied_count: int
    missing_doc_count: int
    high_risk_count: int
    analysis_source: AnalysisSource | None = None


class AnalyzeResponse(BaseModel):
    """Returned immediately when analysis is triggered."""
    project_id: str
    status: str
    analysis_source: AnalysisSource | None = None
    fallback_reason: str | None = None


class ReportResponse(BaseModel):
    project_id: str
    report_pdf_url: str | None
