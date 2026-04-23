"""
Grant analysis service.

Phase 2/3: returns mocked BrightPath demo data so the API contract is testable
end-to-end before real AI pipelines are wired in (Phase 4).

_ReportRecord is kept here as a private dataclass so this module has no
dependency on app.models.analysis (which is now the SQLAlchemy schema).
Phase 4 will replace this in-memory store with DB-backed ReadinessReport rows.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.schemas.analysis import (
    AnalysisResponse,
    Citation,
    DraftAnswer,
    MissingDocument,
    RequirementResult,
    RiskFlag,
)

@dataclass
class _ReportRecord:
    project_id: str
    eligibility_score: int
    readiness_score: int
    missing_items: list[dict[str, Any]]
    risk_flags: list[dict[str, Any]]
    requirements: list[dict[str, Any]]
    draft_answers: list[dict[str, Any]]
    report_pdf_url: str | None = None
    id: str = field(default_factory=lambda: f"report_{uuid.uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_report_store: dict[str, _ReportRecord] = {}

# ---------------------------------------------------------------------------
# Mock data — mirrors frontend/lib/mock-data.ts BrightPath demo exactly
# ---------------------------------------------------------------------------

_MOCK_REQUIREMENTS: list[RequirementResult] = [
    RequirementResult(
        id="req_1",
        text="Applicant must be a registered 501(c)(3) nonprofit.",
        type="eligibility",
        importance="required",
        status="satisfied",
        confidence=0.95,
        evidence=[
            Citation(
                document_name="Mission Statement.pdf",
                page_number=1,
                summary="Organization identifies as a 501(c)(3) nonprofit incorporated in Ohio.",
            )
        ],
    ),
    RequirementResult(
        id="req_2",
        text="Programs must focus on STEM education or mentoring for youth.",
        type="eligibility",
        importance="required",
        status="satisfied",
        confidence=0.93,
        evidence=[
            Citation(
                document_name="Program Description.pdf",
                page_number=1,
                summary="Core programs include STEM mentoring, coding workshops, and academic tutoring.",
            ),
            Citation(
                document_name="Annual Report.pdf",
                page_number=4,
                summary="2024 programs reached 312 students through STEM workshops and mentoring.",
            ),
        ],
    ),
    RequirementResult(
        id="req_3",
        text="Applicant must serve low-income youth in Ohio.",
        type="eligibility",
        importance="required",
        status="satisfied",
        confidence=0.91,
        evidence=[
            Citation(
                document_name="Program Description.pdf",
                page_number=2,
                summary="Programs exclusively serve Title I schools in Columbus with over 80% free/reduced lunch eligibility.",
            )
        ],
    ),
    RequirementResult(
        id="req_4",
        text="Applicant must provide proof of IRS tax-exempt status.",
        type="required_document",
        importance="required",
        status="not_satisfied",
        confidence=0.0,
        evidence=[],
    ),
    RequirementResult(
        id="req_5",
        text="Organization must have been operational for at least 2 years.",
        type="eligibility",
        importance="required",
        status="satisfied",
        confidence=0.88,
        evidence=[
            Citation(
                document_name="Mission Statement.pdf",
                page_number=1,
                summary="Founded in 2019. Organization has been operating for over 5 years.",
            )
        ],
    ),
    RequirementResult(
        id="req_6",
        text="Applicant must submit a current list of board members.",
        type="required_document",
        importance="required",
        status="not_satisfied",
        confidence=0.0,
        evidence=[],
    ),
    RequirementResult(
        id="req_7",
        text="Grant request must not exceed 25% of annual operating budget.",
        type="budget",
        importance="required",
        status="satisfied",
        confidence=0.90,
        evidence=[
            Citation(
                document_name="Annual Budget.pdf",
                page_number=1,
                summary="Annual operating budget is $420,000. Maximum 25% = $105,000, within grant range.",
            )
        ],
    ),
    RequirementResult(
        id="req_8",
        text="Applicant must demonstrate matching funds of at least 10% of grant request.",
        type="budget",
        importance="required",
        status="partially_satisfied",
        confidence=0.40,
        evidence=[
            Citation(
                document_name="Annual Budget.pdf",
                page_number=2,
                summary="Budget mentions in-kind contributions from school district, but no cash match commitment letter was found.",
            )
        ],
    ),
    RequirementResult(
        id="req_9",
        text="Programs must serve students in grades 6–8.",
        type="eligibility",
        importance="required",
        status="satisfied",
        confidence=0.94,
        evidence=[
            Citation(
                document_name="Program Description.pdf",
                page_number=1,
                summary="All programs target middle school students in grades 6 through 8.",
            )
        ],
    ),
    RequirementResult(
        id="req_10",
        text="Organization must provide a detailed program budget for grant funds.",
        type="narrative",
        importance="required",
        status="partially_satisfied",
        confidence=0.62,
        evidence=[
            Citation(
                document_name="Annual Budget.pdf",
                page_number=3,
                summary="Organizational budget provided. Program-specific line items for grant activities are not fully broken out.",
            )
        ],
    ),
]

_MOCK_MISSING_DOCUMENTS: list[MissingDocument] = [
    MissingDocument(
        name="IRS Determination Letter",
        required=True,
        description="Official IRS letter confirming 501(c)(3) tax-exempt status. Required for eligibility verification.",
    ),
    MissingDocument(
        name="Board of Directors List",
        required=True,
        description="Current list of board members with roles and contact information. Required by most Ohio foundations.",
    ),
    MissingDocument(
        name="Matching Funds Commitment Letter",
        required=False,
        description="Letter confirming a matching funds commitment of at least 10% of the grant request (~$5,000–$15,000).",
    ),
]

_MOCK_RISK_FLAGS: list[RiskFlag] = [
    RiskFlag(
        severity="high",
        title="IRS determination letter not uploaded",
        description="This is a hard eligibility requirement. Without it, the application will be disqualified before review.",
    ),
    RiskFlag(
        severity="high",
        title="Matching funds not documented",
        description="The grant requires a 10% cash match. In-kind contributions alone may not satisfy this requirement. Upload a commitment letter.",
    ),
    RiskFlag(
        severity="medium",
        title="Program budget not itemized",
        description="An organizational budget was uploaded, but grant-specific line items are missing. Add a program budget before submitting.",
    ),
    RiskFlag(
        severity="medium",
        title="Board list not provided",
        description="Most Ohio funders require a current board member list. Upload it to avoid a documentation deficiency.",
    ),
]

_MOCK_DRAFT_ANSWERS: list[DraftAnswer] = [
    DraftAnswer(
        id="draft_1",
        question="Describe your organization's mission and the primary programs you operate.",
        draft_answer=(
            "BrightPath Youth Foundation is a 501(c)(3) nonprofit organization based in Columbus, Ohio, "
            "dedicated to providing after-school STEM mentoring and academic support to low-income middle school students. "
            "Our core programs include weekly STEM workshops, one-on-one coding mentorship, and academic tutoring for students "
            "in grades 6–8 attending Title I schools.\n\n"
            "In 2024, we served 312 students across four Columbus partner schools, achieving a 91% program completion rate "
            "and a measurable improvement in math assessment scores among 74% of participants."
        ),
        citations=[
            Citation(document_name="Mission Statement.pdf", page_number=1, summary="States mission, founding year, and 501(c)(3) status."),
            Citation(document_name="Program Description.pdf", page_number=1, summary="Describes STEM workshops, coding mentorship, and tutoring programs."),
            Citation(document_name="Annual Report.pdf", page_number=4, summary="Reports 312 students served in 2024 with 91% completion rate."),
        ],
        missing_evidence=[],
        confidence=0.91,
    ),
    DraftAnswer(
        id="draft_2",
        question="How does your program specifically serve low-income youth in Ohio, and what is your evidence of need?",
        draft_answer=(
            "BrightPath exclusively partners with Title I middle schools in Columbus, Ohio, where more than 80% of students "
            "qualify for free or reduced-price lunch. Our target population faces significant gaps in access to quality STEM "
            "programming outside of school hours.\n\n"
            "According to our 2024 Annual Report, 78% of students we served had no prior access to organized STEM activities "
            "before joining BrightPath. Our program description references Columbus City Schools data confirming that our partner "
            "schools rank in the bottom quartile for STEM outcomes in Ohio."
        ),
        citations=[
            Citation(document_name="Program Description.pdf", page_number=2, summary="Describes Title I school partnerships and 80%+ free/reduced lunch rate."),
            Citation(document_name="Annual Report.pdf", page_number=6, summary="78% of students had no prior STEM program access."),
        ],
        missing_evidence=[],
        confidence=0.87,
    ),
    DraftAnswer(
        id="draft_3",
        question="What specific outcomes will this grant support, and how will you measure success?",
        draft_answer=(
            "This grant will support expansion of our STEM mentoring program to two additional Columbus partner schools, "
            "adding capacity to serve approximately 120 new students annually.\n\n"
            "Success will be measured through: (1) student participation rates and program completion, tracked via attendance "
            "records; (2) pre/post STEM interest and confidence surveys; and (3) academic performance in math and science, "
            "tracked in partnership with schools.\n\n"
            "Note: Specific outcome targets for the new expansion sites are not yet documented in uploaded materials. "
            "We recommend adding projected outcomes and measurable milestones to your program description before final submission."
        ),
        citations=[
            Citation(document_name="Program Description.pdf", page_number=3, summary="Describes current outcomes tracking methodology for existing programs."),
            Citation(document_name="Annual Report.pdf", page_number=5, summary="Reports outcomes methodology and 2024 performance benchmarks."),
        ],
        missing_evidence=[
            "Specific outcome targets and measurable projections for new program expansion sites are not documented in the uploaded materials."
        ],
        confidence=0.72,
    ),
]


def run_analysis(project_id: str) -> _ReportRecord:
    """
    Triggers analysis for a project and stores the result.

    Phase 2: returns deterministic mock data.
    Phase 4: will call grant_extractor → evidence_matcher → readiness_scorer → application_drafter.
    """
    report = _ReportRecord(
        project_id=project_id,
        eligibility_score=82,
        readiness_score=74,
        missing_items=[m.model_dump() for m in _MOCK_MISSING_DOCUMENTS],
        risk_flags=[r.model_dump() for r in _MOCK_RISK_FLAGS],
        requirements=[r.model_dump() for r in _MOCK_REQUIREMENTS],
        draft_answers=[d.model_dump() for d in _MOCK_DRAFT_ANSWERS],
        report_pdf_url=None,
    )
    _report_store[project_id] = report
    return report


def get_analysis(project_id: str) -> _ReportRecord | None:
    return _report_store.get(project_id)


def build_analysis_response(report: _ReportRecord) -> AnalysisResponse:
    return AnalysisResponse(
        project_id=report.project_id,
        eligibility_score=report.eligibility_score,
        readiness_score=report.readiness_score,
        requirements=[RequirementResult(**r) for r in report.requirements],
        missing_documents=[MissingDocument(**m) for m in report.missing_items],
        risk_flags=[RiskFlag(**f) for f in report.risk_flags],
        draft_answers=[DraftAnswer(**d) for d in report.draft_answers],
    )
