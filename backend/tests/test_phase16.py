"""
Phase 16 tests: TXT parsing, real-pipeline provenance, and re-analysis.

All LLM calls are monkeypatched at the USE SITE (the importing service module).
TF-IDF embeddings are used — no API key required for embedding tests.
"""
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_EXTRACTION_RESPONSE = {
    "grant_name": "Community STEM Fund",
    "funder_name": "Lakeshore Foundation",
    "deadline": "May 15, 2026",
    "eligibility_requirements": [
        {
            "text": "Applicant must be a 501(c)(3) nonprofit.",
            "required": True,
            "category": "eligibility",
            "source_quote": None,
        },
        {
            "text": "Programs must serve youth in Ohio.",
            "required": True,
            "category": "eligibility",
            "source_quote": None,
        },
    ],
    "required_documents": [
        {"document_name": "IRS determination letter", "required": True},
    ],
    "narrative_questions": [
        {"question": "Describe your mission and primary programs.", "topic": "mission"},
    ],
    "budget_requirements": ["Grant request must not exceed 25% of annual budget."],
    "risk_flags": [],
}

_MATCH_RESPONSE = {
    "status": "satisfied",
    "confidence": 0.87,
    "explanation": "Evidence clearly satisfies the requirement.",
    "supporting_citations": [
        {
            "document_name": "mission-statement.txt",
            "page_number": 1,
            "summary": "Organization is a 501(c)(3) registered nonprofit.",
        }
    ],
    "missing_evidence": [],
}

_DRAFT_RESPONSE = {
    "draft_answer": "Horizon Youth Collective is a 501(c)(3) nonprofit serving youth in Columbus, Ohio through STEM mentoring.",
    "citations": [
        {
            "document_name": "mission-statement.txt",
            "page_number": 1,
            "summary": "Mission statement confirms 501(c)(3) status and STEM focus.",
        }
    ],
    "missing_evidence": [],
    "confidence": 0.82,
    "suggested_improvements": [],
}

_GRANT_TEXT = """\
COMMUNITY STEM ACCESS FUND — REQUEST FOR PROPOSALS

ELIGIBILITY REQUIREMENTS

Applicants must meet all of the following:

1. Must be a 501(c)(3) nonprofit organization in good standing with the IRS.
   An IRS determination letter is required.

2. Programs must serve youth residing in the state of Ohio.

3. Annual operating budget must be between $100,000 and $2,000,000.
   A current Form 990 is required.

NARRATIVE QUESTIONS

Q1. Describe your organization's mission and how your STEM program serves
the target population. (500 words max)

BUDGET GUIDANCE

Grant request must not exceed 25% of annual operating budget.
"""

_MISSION_TEXT = """\
Horizon Youth Collective is a 501(c)(3) nonprofit dedicated to empowering
low-income youth in Columbus, Ohio through hands-on STEM education and
near-peer mentoring. Founded in 2019, we serve over 112 students annually.

Annual operating budget: $485,000. We are in good standing with the IRS
(EIN: 88-0000000). Our programs operate in Franklin County, Ohio.
"""


def _upload_txt(
    client: TestClient,
    org_id: str,
    project_id: str,
    doc_type: str,
    filename: str,
    text: str,
) -> dict:
    content = text.encode("utf-8")
    resp = client.post(
        "/documents/upload",
        data={
            "organization_id": org_id,
            "project_id": project_id,
            "document_type": doc_type,
        },
        files={"file": (filename, io.BytesIO(content), "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# TXT parsing
# ---------------------------------------------------------------------------


class TestTxtParsing:
    def test_txt_upload_status_is_parsed(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        doc = _upload_txt(
            client, org_id, project_id, "mission_statement",
            "mission.txt", _MISSION_TEXT,
        )
        assert doc["status"] == "parsed"

    def test_txt_upload_creates_chunks(
        self, client: TestClient, org_id: str, project_id: str, db_session: Session
    ) -> None:
        from app.models.chunk import DocumentChunk

        _upload_txt(
            client, org_id, project_id, "mission_statement",
            "mission.txt", _MISSION_TEXT,
        )
        chunks = db_session.query(DocumentChunk).all()
        assert len(chunks) >= 1
        assert all(c.chunk_text for c in chunks)

    def test_txt_upload_page_count_is_one(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        _upload_txt(
            client, org_id, project_id, "mission_statement",
            "mission.txt", _MISSION_TEXT,
        )
        # page_count is on DocumentResponse (list endpoint), not DocumentSummary (upload endpoint)
        docs = client.get(f"/projects/{project_id}/documents").json()
        doc = next(d for d in docs if d["filename"] == "mission.txt")
        assert doc["page_count"] == 1

    def test_txt_grant_doc_enables_real_pipeline(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        db_session: Session,
        monkeypatch,
    ) -> None:
        """A TXT grant_opportunity document should let the real pipeline run."""
        import app.services.grant_extractor as ge
        import app.services.evidence_matcher as em
        import app.services.application_drafter as ad
        from app.core.config import settings

        monkeypatch.setattr(settings, "anthropic_api_key", "fake_key_for_test")
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: _EXTRACTION_RESPONSE)
        monkeypatch.setattr(em, "call_claude_json", lambda **kw: _MATCH_RESPONSE)
        monkeypatch.setattr(ad, "call_claude_json", lambda **kw: _DRAFT_RESPONSE)

        _upload_txt(
            client, org_id, project_id, "grant_opportunity",
            "grant.txt", _GRANT_TEXT,
        )
        _upload_txt(
            client, org_id, project_id, "mission_statement",
            "mission.txt", _MISSION_TEXT,
        )

        resp = client.post(f"/projects/{project_id}/analyze")
        assert resp.status_code == 200
        body = resp.json()
        assert body["analysis_source"] == "real_pipeline"

        analysis = client.get(f"/projects/{project_id}/analysis").json()
        assert analysis["analysis_source"] == "real_pipeline"
        assert analysis["fallback_reason"] is None
        # _EXTRACTION_RESPONSE has 2 eligibility + 1 doc + 1 narrative + 1 budget = 5
        assert len(analysis["requirements"]) == 5

    def test_txt_empty_file_does_not_crash(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        """An empty TXT file should be stored without error (parse_failed is acceptable)."""
        resp = client.post(
            "/documents/upload",
            data={
                "organization_id": org_id,
                "project_id": project_id,
                "document_type": "other",
            },
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        assert resp.status_code == 201
        # Empty TXT → no text → status stored (not parse_failed; parse_txt_bytes returns [])
        assert resp.json()["status"] in ("stored", "parsed", "parse_failed")


# ---------------------------------------------------------------------------
# Provenance fields
# ---------------------------------------------------------------------------


class TestProvenanceFields:
    def test_no_docs_fallback_has_correct_source(
        self, client: TestClient, project_id: str
    ) -> None:
        """No documents uploaded → fallback_mock with no-docs reason."""
        body = client.post(f"/projects/{project_id}/analyze").json()
        assert body["analysis_source"] == "fallback_mock"
        assert body["fallback_reason"] is not None
        assert "No documents" in body["fallback_reason"] or "uploaded" in body["fallback_reason"].lower()

    def test_no_grant_doc_fallback_has_correct_source(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        """Docs uploaded but no grant_opportunity → fallback_mock with grant-doc reason."""
        _upload_txt(
            client, org_id, project_id, "mission_statement",
            "mission.txt", _MISSION_TEXT,
        )
        body = client.post(f"/projects/{project_id}/analyze").json()
        assert body["analysis_source"] == "fallback_mock"
        assert "Grant Opportunity" in body["fallback_reason"]

    def test_no_api_key_fallback_has_correct_source(
        self, client: TestClient, org_id: str, project_id: str, monkeypatch
    ) -> None:
        """Grant doc present but API key missing → fallback_mock with api-key reason."""
        from app.core.config import settings
        monkeypatch.setattr(settings, "anthropic_api_key", "")

        _upload_txt(client, org_id, project_id, "grant_opportunity", "grant.txt", _GRANT_TEXT)
        _upload_txt(client, org_id, project_id, "mission_statement", "mission.txt", _MISSION_TEXT)

        body = client.post(f"/projects/{project_id}/analyze").json()
        assert body["analysis_source"] == "fallback_mock"
        assert body["fallback_reason"] is not None

    def test_real_pipeline_source_in_get_analysis(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        monkeypatch,
    ) -> None:
        """GET /analysis exposes analysis_source=real_pipeline after a successful run."""
        import app.services.grant_extractor as ge
        import app.services.evidence_matcher as em
        import app.services.application_drafter as ad
        from app.core.config import settings

        monkeypatch.setattr(settings, "anthropic_api_key", "fake_key_for_test")
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: _EXTRACTION_RESPONSE)
        monkeypatch.setattr(em, "call_claude_json", lambda **kw: _MATCH_RESPONSE)
        monkeypatch.setattr(ad, "call_claude_json", lambda **kw: _DRAFT_RESPONSE)

        _upload_txt(client, org_id, project_id, "grant_opportunity", "grant.txt", _GRANT_TEXT)
        _upload_txt(client, org_id, project_id, "mission_statement", "mission.txt", _MISSION_TEXT)
        client.post(f"/projects/{project_id}/analyze")

        analysis = client.get(f"/projects/{project_id}/analysis").json()
        assert analysis["analysis_source"] == "real_pipeline"
        assert analysis["fallback_reason"] is None

    def test_diagnostics_reflect_uploaded_txt_docs(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        monkeypatch,
    ) -> None:
        """Diagnostics block correctly counts TXT-parsed docs and chunks."""
        import app.services.grant_extractor as ge
        import app.services.evidence_matcher as em
        import app.services.application_drafter as ad
        from app.core.config import settings

        monkeypatch.setattr(settings, "anthropic_api_key", "fake_key_for_test")
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: _EXTRACTION_RESPONSE)
        monkeypatch.setattr(em, "call_claude_json", lambda **kw: _MATCH_RESPONSE)
        monkeypatch.setattr(ad, "call_claude_json", lambda **kw: _DRAFT_RESPONSE)

        _upload_txt(client, org_id, project_id, "grant_opportunity", "grant.txt", _GRANT_TEXT)
        _upload_txt(client, org_id, project_id, "mission_statement", "mission.txt", _MISSION_TEXT)
        client.post(f"/projects/{project_id}/analyze")

        diag = client.get(f"/projects/{project_id}/analysis").json()["diagnostics"]
        assert diag["uploaded_doc_count"] == 2
        assert diag["parsed_doc_count"] == 2
        assert diag["chunk_count"] >= 2
        assert diag["grant_opportunity_found"] is True
        assert diag["extracted_requirement_count"] == 5
        assert diag["embeddings_generated"] is True


# ---------------------------------------------------------------------------
# Re-analysis
# ---------------------------------------------------------------------------


class TestReanalysis:
    def test_reanalysis_updates_source_from_fallback_to_real(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        monkeypatch,
    ) -> None:
        """First run without grant doc → fallback. Second run with grant doc + key → real_pipeline."""
        import app.services.grant_extractor as ge
        import app.services.evidence_matcher as em
        import app.services.application_drafter as ad
        from app.core.config import settings

        # First run: no grant doc → fallback
        _upload_txt(client, org_id, project_id, "mission_statement", "mission.txt", _MISSION_TEXT)
        first = client.post(f"/projects/{project_id}/analyze").json()
        assert first["analysis_source"] == "fallback_mock"

        # Upload grant doc + set fake API key
        _upload_txt(client, org_id, project_id, "grant_opportunity", "grant.txt", _GRANT_TEXT)
        monkeypatch.setattr(settings, "anthropic_api_key", "fake_key_for_test")
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: _EXTRACTION_RESPONSE)
        monkeypatch.setattr(em, "call_claude_json", lambda **kw: _MATCH_RESPONSE)
        monkeypatch.setattr(ad, "call_claude_json", lambda **kw: _DRAFT_RESPONSE)

        # Second run: now has grant doc + key → real pipeline
        second = client.post(f"/projects/{project_id}/analyze").json()
        assert second["analysis_source"] == "real_pipeline"

        # GET /analysis also reflects updated source
        analysis = client.get(f"/projects/{project_id}/analysis").json()
        assert analysis["analysis_source"] == "real_pipeline"

    def test_reanalysis_clears_stale_pdf_url(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        db_session: Session,
    ) -> None:
        """Re-running analysis clears the cached report_pdf_url so the PDF is regenerated."""
        from app.models.analysis import ReadinessReport

        client.post(f"/projects/{project_id}/analyze")
        client.post(f"/projects/{project_id}/analyze")

        db_session.expire_all()
        report = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        assert report is not None
        # report_pdf_url is cleared on every re-analysis
        assert report.report_pdf_url is None
