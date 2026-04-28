"""
Grant analysis orchestrator.

Dispatch logic:
  - real_pipeline: grant_opportunity document uploaded + ANTHROPIC_API_KEY set.
    Claude extracts requirements, matches evidence in uploaded docs, scores.
  - fallback_mock: any other case — missing grant doc, missing API key, or
    pipeline error. Returns deterministic BrightPath demo data.
  - seeded_demo: set externally by seed.py for the startup demo project.

Results are always persisted to ReadinessReport so GET /analysis is consistent.
analysis_source and fallback_reason are stored on the report and returned in
the API response so the UI can surface provenance transparently.
"""
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import ReadinessReport
from app.schemas.analysis import (
    AnalysisDiagnostics,
    AnalysisResponse,
    Citation,
    DraftAnswer,
    MissingDocument,
    RequirementResult,
    RiskFlag,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback reason constants (safe for user display)
# ---------------------------------------------------------------------------
REASON_NO_GRANT_DOC = (
    "No Grant Opportunity Document uploaded. "
    "Add the grant RFP or announcement as a Grant Opportunity Document, then Re-analyze."
)
REASON_NO_API_KEY = (
    "AI analysis is not enabled on this server. "
    "Sample results are shown — contact the administrator to enable real analysis."
)
REASON_NO_DOCS = (
    "No documents uploaded yet. "
    "Add nonprofit documents and a Grant Opportunity Document, then Re-analyze."
)
REASON_NO_REQUIREMENTS = (
    "No requirements could be extracted from the grant document. "
    "Ensure the file contains readable text (PDF or TXT), then Re-analyze."
)
REASON_PIPELINE_ERROR = (
    "The AI pipeline encountered an error and fell back to sample data. "
    "Try Re-analyzing — if the problem persists, ensure your documents are readable."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_analysis(project_id: str, db: Session) -> str:
    """Orchestrate grant analysis. Returns the analysis_source that was used."""
    from app.models.document import Document

    docs = (
        db.query(Document)
        .filter(Document.project_id == project_id)
        .all()
    )
    has_uploaded_docs = len(docs) > 0

    grant_doc = next(
        (d for d in docs
         if d.document_type == "grant_opportunity"
         and d.status in ("parsed", "stored")),
        None,
    )
    has_grant_doc = grant_doc is not None
    api_key_set = bool(settings.anthropic_api_key)

    logger.info(
        "[%s] Analysis dispatch: docs=%d grant_doc=%s api_key=%s",
        project_id, len(docs), has_grant_doc, api_key_set,
    )

    if not has_uploaded_docs:
        reason = REASON_NO_DOCS
        logger.info("[%s] Fallback (no_docs): %s", project_id, reason)
        _run_mock_analysis(project_id, db, fallback_reason=reason)
        return "fallback_mock"

    if not has_grant_doc:
        reason = REASON_NO_GRANT_DOC
        logger.info("[%s] Fallback (no_grant_doc): %s", project_id, reason)
        _run_mock_analysis(project_id, db, fallback_reason=reason)
        return "fallback_mock"

    if not api_key_set:
        reason = REASON_NO_API_KEY
        logger.info("[%s] Fallback (no_api_key): %s", project_id, reason)
        _run_mock_analysis(project_id, db, fallback_reason=reason)
        return "fallback_mock"

    # All conditions met — attempt real pipeline
    try:
        _run_real_analysis(project_id, db)
        logger.info("[%s] Real pipeline completed successfully.", project_id)
        return "real_pipeline"
    except Exception as exc:
        logger.error(
            "[%s] Real pipeline failed, falling back to mock: %s",
            project_id, exc,
        )
        _run_mock_analysis(project_id, db, fallback_reason=REASON_PIPELINE_ERROR)
        return "fallback_mock"


def get_analysis(project_id: str, db: Session) -> ReadinessReport | None:
    return (
        db.query(ReadinessReport)
        .filter(ReadinessReport.project_id == project_id)
        .first()
    )


def build_analysis_response(report: ReadinessReport, db: Session | None = None) -> AnalysisResponse:
    diagnostics = _compute_diagnostics(report.project_id, db) if db else None
    return AnalysisResponse(
        project_id=report.project_id,
        eligibility_score=report.eligibility_score,
        readiness_score=report.readiness_score,
        requirements=[RequirementResult(**r) for r in report.requirements],
        missing_documents=[MissingDocument(**m) for m in report.missing_items],
        risk_flags=[RiskFlag(**f) for f in report.risk_flags],
        draft_answers=[DraftAnswer(**d) for d in report.draft_answers],
        analysis_source=report.analysis_source,  # type: ignore[arg-type]
        fallback_reason=report.fallback_reason,
        diagnostics=diagnostics,
    )


# ---------------------------------------------------------------------------
# Real AI pipeline
# ---------------------------------------------------------------------------

def _run_real_analysis(project_id: str, db: Session) -> None:
    from app.services import (
        application_drafter,
        embedding_service,
        evidence_matcher,
        grant_extractor,
        readiness_scorer,
    )

    logger.info("[%s] Stage 1/6: Embedding document chunks...", project_id)
    embedded_count = embedding_service.embed_chunks_for_project(db, project_id)
    logger.info("[%s]   Embedded %d chunks.", project_id, embedded_count)

    logger.info("[%s] Stage 2/6: Extracting grant requirements...", project_id)
    requirements = grant_extractor.extract_requirements(db, project_id)
    logger.info("[%s]   Extracted %d requirements.", project_id, len(requirements))

    if not requirements:
        logger.warning("[%s] No requirements extracted — falling back to mock.", project_id)
        _run_mock_analysis(project_id, db, fallback_reason=REASON_NO_REQUIREMENTS)
        return

    logger.info("[%s] Stage 3/6: Matching requirements to evidence...", project_id)
    match_results = evidence_matcher.match_all_requirements(db, requirements, project_id)
    logger.info("[%s]   Matched %d requirements.", project_id, len(match_results))

    logger.info("[%s] Stage 4/6: Computing scores...", project_id)
    matches_only = {rid: result[0] for rid, result in match_results.items()}
    eligibility_score, readiness_score = readiness_scorer.compute_scores(requirements, matches_only)
    logger.info(
        "[%s]   Eligibility=%d  Readiness=%d",
        project_id, eligibility_score, readiness_score,
    )

    logger.info("[%s] Stage 5/6: Generating risk flags and missing docs...", project_id)
    risk_flags = readiness_scorer.generate_risk_flags(requirements, matches_only)
    missing_docs = readiness_scorer.generate_missing_documents(requirements, matches_only)
    logger.info(
        "[%s]   %d risk flags, %d missing docs.", project_id, len(risk_flags), len(missing_docs)
    )

    logger.info("[%s] Stage 6/6: Drafting answers for narrative questions...", project_id)
    req_results = readiness_scorer.build_requirement_results(requirements, match_results)
    draft_answers = application_drafter.draft_answers(db, project_id, requirements, match_results)
    logger.info("[%s]   Drafted %d answers.", project_id, len(draft_answers))

    _upsert_report(
        db=db,
        project_id=project_id,
        eligibility_score=eligibility_score,
        readiness_score=readiness_score,
        requirements=req_results,
        missing_docs=[m.model_dump() for m in missing_docs],
        risk_flags=[f.model_dump() for f in risk_flags],
        draft_answers=[d.model_dump() for d in draft_answers],
        analysis_source="real_pipeline",
    )


# ---------------------------------------------------------------------------
# Mock fallback — BrightPath demo data
# ---------------------------------------------------------------------------

_MOCK_REQUIREMENTS: list[dict] = [
    {"id": "req_1", "text": "Applicant must be a registered 501(c)(3) nonprofit.", "type": "eligibility", "importance": "required", "status": "satisfied", "confidence": 0.95, "evidence": [{"document_name": "Mission Statement.pdf", "page_number": 1, "summary": "Organization identifies as a 501(c)(3) nonprofit incorporated in Ohio."}]},
    {"id": "req_2", "text": "Programs must focus on STEM education or mentoring for youth.", "type": "eligibility", "importance": "required", "status": "satisfied", "confidence": 0.93, "evidence": [{"document_name": "Program Description.pdf", "page_number": 1, "summary": "Core programs include STEM mentoring, coding workshops, and academic tutoring."}, {"document_name": "Annual Report.pdf", "page_number": 4, "summary": "2024 programs reached 312 students through STEM workshops and mentoring."}]},
    {"id": "req_3", "text": "Applicant must serve low-income youth in Ohio.", "type": "eligibility", "importance": "required", "status": "satisfied", "confidence": 0.91, "evidence": [{"document_name": "Program Description.pdf", "page_number": 2, "summary": "Programs exclusively serve Title I schools in Columbus with over 80% free/reduced lunch eligibility."}]},
    {"id": "req_4", "text": "Applicant must provide proof of IRS tax-exempt status.", "type": "required_document", "importance": "required", "status": "not_satisfied", "confidence": 0.0, "evidence": []},
    {"id": "req_5", "text": "Organization must have been operational for at least 2 years.", "type": "eligibility", "importance": "required", "status": "satisfied", "confidence": 0.88, "evidence": [{"document_name": "Mission Statement.pdf", "page_number": 1, "summary": "Founded in 2019. Organization has been operating for over 5 years."}]},
    {"id": "req_6", "text": "Applicant must submit a current list of board members.", "type": "required_document", "importance": "required", "status": "not_satisfied", "confidence": 0.0, "evidence": []},
    {"id": "req_7", "text": "Grant request must not exceed 25% of annual operating budget.", "type": "budget", "importance": "required", "status": "satisfied", "confidence": 0.90, "evidence": [{"document_name": "Annual Budget.pdf", "page_number": 1, "summary": "Annual operating budget is $420,000. Maximum 25% = $105,000, within grant range."}]},
    {"id": "req_8", "text": "Applicant must demonstrate matching funds of at least 10% of grant request.", "type": "budget", "importance": "required", "status": "partially_satisfied", "confidence": 0.40, "evidence": [{"document_name": "Annual Budget.pdf", "page_number": 2, "summary": "Budget mentions in-kind contributions from school district, but no cash match commitment letter was found."}]},
    {"id": "req_9", "text": "Programs must serve students in grades 6–8.", "type": "eligibility", "importance": "required", "status": "satisfied", "confidence": 0.94, "evidence": [{"document_name": "Program Description.pdf", "page_number": 1, "summary": "All programs target middle school students in grades 6 through 8."}]},
    {"id": "req_10", "text": "Organization must provide a detailed program budget for grant funds.", "type": "narrative", "importance": "required", "status": "partially_satisfied", "confidence": 0.62, "evidence": [{"document_name": "Annual Budget.pdf", "page_number": 3, "summary": "Organizational budget provided. Program-specific line items for grant activities are not fully broken out."}]},
]

_MOCK_MISSING_DOCS: list[dict] = [
    {"name": "IRS Determination Letter", "required": True, "description": "Official IRS letter confirming 501(c)(3) tax-exempt status. Required for eligibility verification."},
    {"name": "Board of Directors List", "required": True, "description": "Current list of board members with roles and contact information. Required by most Ohio foundations."},
    {"name": "Matching Funds Commitment Letter", "required": False, "description": "Letter confirming a matching funds commitment of at least 10% of the grant request (~$5,000–$15,000)."},
]

_MOCK_RISK_FLAGS: list[dict] = [
    {"severity": "high", "title": "IRS determination letter not uploaded", "description": "This is a hard eligibility requirement. Without it, the application will be disqualified before review."},
    {"severity": "high", "title": "Matching funds not documented", "description": "The grant requires a 10% cash match. In-kind contributions alone may not satisfy this requirement. Upload a commitment letter."},
    {"severity": "medium", "title": "Program budget not itemized", "description": "An organizational budget was uploaded, but grant-specific line items are missing. Add a program budget before submitting."},
    {"severity": "medium", "title": "Board list not provided", "description": "Most Ohio funders require a current board member list. Upload it to avoid a documentation deficiency."},
]

_MOCK_DRAFT_ANSWERS: list[dict] = [
    {
        "id": "draft_1",
        "question": "Describe your organization's mission and the primary programs you operate.",
        "draft_answer": (
            "BrightPath Youth Foundation is a 501(c)(3) nonprofit organization based in Columbus, Ohio, "
            "dedicated to providing after-school STEM mentoring and academic support to low-income middle school students. "
            "Our core programs include weekly STEM workshops, one-on-one coding mentorship, and academic tutoring for students "
            "in grades 6–8 attending Title I schools.\n\n"
            "In 2024, we served 312 students across four Columbus partner schools, achieving a 91% program completion rate "
            "and a measurable improvement in math assessment scores among 74% of participants."
        ),
        "citations": [
            {"document_name": "Mission Statement.pdf", "page_number": 1, "summary": "States mission, founding year, and 501(c)(3) status."},
            {"document_name": "Program Description.pdf", "page_number": 1, "summary": "Describes STEM workshops, coding mentorship, and tutoring programs."},
            {"document_name": "Annual Report.pdf", "page_number": 4, "summary": "Reports 312 students served in 2024 with 91% completion rate."},
        ],
        "missing_evidence": [],
        "confidence": 0.91,
    },
    {
        "id": "draft_2",
        "question": "How does your program specifically serve low-income youth in Ohio, and what is your evidence of need?",
        "draft_answer": (
            "BrightPath exclusively partners with Title I middle schools in Columbus, Ohio, where more than 80% of students "
            "qualify for free or reduced-price lunch. Our target population faces significant gaps in access to quality STEM "
            "programming outside of school hours.\n\n"
            "According to our 2024 Annual Report, 78% of students we served had no prior access to organized STEM activities "
            "before joining BrightPath. Our program description references Columbus City Schools data confirming that our partner "
            "schools rank in the bottom quartile for STEM outcomes in Ohio."
        ),
        "citations": [
            {"document_name": "Program Description.pdf", "page_number": 2, "summary": "Describes Title I school partnerships and 80%+ free/reduced lunch rate."},
            {"document_name": "Annual Report.pdf", "page_number": 6, "summary": "78% of students had no prior STEM program access."},
        ],
        "missing_evidence": [],
        "confidence": 0.87,
    },
    {
        "id": "draft_3",
        "question": "What specific outcomes will this grant support, and how will you measure success?",
        "draft_answer": (
            "This grant will support expansion of our STEM mentoring program to two additional Columbus partner schools, "
            "adding capacity to serve approximately 120 new students annually.\n\n"
            "Success will be measured through: (1) student participation rates and program completion, tracked via attendance "
            "records; (2) pre/post STEM interest and confidence surveys; and (3) academic performance in math and science, "
            "tracked in partnership with schools.\n\n"
            "Note: Specific outcome targets for the new expansion sites are not yet documented in uploaded materials. "
            "We recommend adding projected outcomes and measurable milestones to your program description before final submission."
        ),
        "citations": [
            {"document_name": "Program Description.pdf", "page_number": 3, "summary": "Describes current outcomes tracking methodology for existing programs."},
            {"document_name": "Annual Report.pdf", "page_number": 5, "summary": "Reports outcomes methodology and 2024 performance benchmarks."},
        ],
        "missing_evidence": [
            "Specific outcome targets and measurable projections for new program expansion sites are not documented in the uploaded materials."
        ],
        "confidence": 0.72,
    },
]


def _run_mock_analysis(
    project_id: str,
    db: Session,
    fallback_reason: str | None = None,
    analysis_source: str = "fallback_mock",
) -> None:
    _upsert_report(
        db=db,
        project_id=project_id,
        eligibility_score=82,
        readiness_score=74,
        requirements=_MOCK_REQUIREMENTS,
        missing_docs=_MOCK_MISSING_DOCS,
        risk_flags=_MOCK_RISK_FLAGS,
        draft_answers=_MOCK_DRAFT_ANSWERS,
        analysis_source=analysis_source,
        fallback_reason=fallback_reason,
    )


# ---------------------------------------------------------------------------
# Diagnostics (computed on-the-fly, no secrets or raw prompts exposed)
# ---------------------------------------------------------------------------

def _compute_diagnostics(project_id: str, db: Session) -> AnalysisDiagnostics:
    from app.models.chunk import DocumentChunk
    from app.models.document import Document
    from app.models.analysis import GrantRequirement

    docs = db.query(Document).filter(Document.project_id == project_id).all()
    parsed_docs = [d for d in docs if d.status == "parsed"]
    grant_doc_found = any(d.document_type == "grant_opportunity" for d in docs)

    chunk_count = (
        db.query(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(Document.project_id == project_id)
        .count()
    )
    embedded_count = (
        db.query(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(
            Document.project_id == project_id,
            DocumentChunk.embedding_json.isnot(None),
        )
        .count()
    )
    req_count = (
        db.query(GrantRequirement)
        .filter(GrantRequirement.project_id == project_id)
        .count()
    )

    return AnalysisDiagnostics(
        uploaded_doc_count=len(docs),
        parsed_doc_count=len(parsed_docs),
        chunk_count=chunk_count,
        grant_opportunity_found=grant_doc_found,
        extracted_requirement_count=req_count,
        embeddings_generated=embedded_count > 0,
    )


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------

def _upsert_report(
    db: Session,
    project_id: str,
    eligibility_score: int,
    readiness_score: int,
    requirements: list[dict],
    missing_docs: list[dict],
    risk_flags: list[dict],
    draft_answers: list[dict],
    analysis_source: str = "fallback_mock",
    fallback_reason: str | None = None,
) -> ReadinessReport:
    existing = (
        db.query(ReadinessReport)
        .filter(ReadinessReport.project_id == project_id)
        .first()
    )

    if existing:
        existing.eligibility_score = eligibility_score
        existing.readiness_score = readiness_score
        existing.requirements = requirements
        existing.missing_items = missing_docs
        existing.risk_flags = risk_flags
        existing.draft_answers = draft_answers
        existing.analysis_source = analysis_source
        existing.fallback_reason = fallback_reason
        existing.report_pdf_url = None  # clear stale PDF
        db.flush()
        return existing

    report = ReadinessReport(
        id=f"report_{uuid.uuid4().hex[:8]}",
        project_id=project_id,
        eligibility_score=eligibility_score,
        readiness_score=readiness_score,
        requirements=requirements,
        missing_items=missing_docs,
        risk_flags=risk_flags,
        draft_answers=draft_answers,
        analysis_source=analysis_source,
        fallback_reason=fallback_reason,
    )
    db.add(report)
    db.flush()
    return report
