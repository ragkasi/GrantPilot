"""
Phase 4 pipeline tests: requirement extraction, evidence matching,
deterministic scoring, draft answers, and fallback-to-mock behavior.

All LLM calls are monkeypatched at the USE SITE (the importing service module),
not at the definition site, because each service does `from app.core.llm import
call_claude_json` which binds the name locally.

Embedding tests use the default TF-IDF backend which needs no API key.
"""
import io
import uuid
from types import SimpleNamespace

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _upload_pdf(
    client: TestClient,
    org_id: str,
    project_id: str,
    doc_type: str,
    filename: str,
    text: str,
) -> dict:
    resp = client.post(
        "/documents/upload",
        data={"organization_id": org_id, "project_id": project_id, "document_type": doc_type},
        files={"file": (filename, io.BytesIO(_make_pdf(text)), "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _req(req_type: str, importance: str = "required") -> SimpleNamespace:
    return SimpleNamespace(
        id=f"req_{uuid.uuid4().hex[:8]}",
        requirement_type=req_type,
        requirement_text=f"Test {req_type} requirement",
        importance=importance,
    )


def _match(status: str, score: float = 0.9) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        match_score=score,
        explanation=f"Explanation for {status}",
    )


# ---------------------------------------------------------------------------
# Embedding service
# ---------------------------------------------------------------------------

class TestEmbeddingService:
    def test_embed_text_returns_float_list(self):
        from app.services.embedding_service import embed_text
        vec = embed_text("STEM programs for low-income youth in Ohio")
        assert isinstance(vec, list)
        assert len(vec) == 256
        assert all(isinstance(x, float) for x in vec)

    def test_embed_text_is_normalised(self):
        import math
        from app.services.embedding_service import embed_text
        vec = embed_text("Grant requires 501c3 status and two years operation")
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 1e-6

    def test_cosine_similarity_identical(self):
        from app.services.embedding_service import cosine_similarity, embed_text
        vec = embed_text("youth STEM mentoring program Columbus Ohio")
        assert cosine_similarity(vec, vec) == pytest.approx(1.0, abs=1e-5)

    def test_cosine_similarity_range(self):
        from app.services.embedding_service import cosine_similarity, embed_text
        a = embed_text("youth STEM mentoring program Columbus Ohio")
        b = embed_text("quarterly financial report audit balance sheet")
        sim = cosine_similarity(a, b)
        assert 0.0 <= sim <= 1.0

    def test_embed_chunks_for_project_populates_embeddings(
        self, client: TestClient, org_id: str, project_id: str, db_session: Session
    ):
        from app.models.chunk import DocumentChunk
        from app.models.document import Document
        from app.services.embedding_service import embed_chunks_for_project

        _upload_pdf(
            client, org_id, project_id, "annual_report", "report.pdf",
            "BrightPath serves 312 youth in Columbus through STEM mentoring programs annually.",
        )
        count = embed_chunks_for_project(db_session, project_id)
        assert count >= 1

        chunks = (
            db_session.query(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.project_id == project_id)
            .all()
        )
        assert all(c.embedding_json is not None for c in chunks)
        assert all(isinstance(c.embedding_json, list) for c in chunks)

    def test_find_similar_chunks_returns_ranked_results(
        self, client: TestClient, org_id: str, project_id: str, db_session: Session
    ):
        from app.services.embedding_service import embed_chunks_for_project, find_similar_chunks

        _upload_pdf(
            client, org_id, project_id, "annual_report", "annual.pdf",
            "Our STEM program served three hundred twelve students in 2024 across Columbus Ohio schools.",
        )
        _upload_pdf(
            client, org_id, project_id, "budget", "budget.pdf",
            "Annual operating budget is four hundred twenty thousand dollars for fiscal year 2024.",
        )
        embed_chunks_for_project(db_session, project_id)
        results = find_similar_chunks(
            db_session,
            query_text="number of students served by STEM program",
            project_id=project_id,
            top_k=3,
        )
        assert len(results) <= 3
        assert all(hasattr(r, "chunk_text") for r in results)


# ---------------------------------------------------------------------------
# Readiness scorer (fully deterministic — no mocking needed)
# ---------------------------------------------------------------------------

class TestReadinessScorer:
    def test_all_satisfied_gives_100(self):
        from app.services.readiness_scorer import compute_scores
        reqs = [_req("eligibility"), _req("eligibility")]
        matches = {r.id: _match("satisfied") for r in reqs}
        elig, ready = compute_scores(reqs, matches)
        assert elig == 100
        assert ready == 100

    def test_all_not_satisfied_gives_0(self):
        from app.services.readiness_scorer import compute_scores
        reqs = [_req("eligibility"), _req("required_document")]
        matches = {r.id: _match("not_satisfied") for r in reqs}
        elig, ready = compute_scores(reqs, matches)
        assert elig == 0
        assert ready == 0

    def test_mixed_statuses_score_between_0_and_100(self):
        from app.services.readiness_scorer import compute_scores
        reqs = [_req("eligibility"), _req("eligibility"), _req("required_document")]
        matches = {
            reqs[0].id: _match("satisfied"),
            reqs[1].id: _match("partially_satisfied"),
            reqs[2].id: _match("not_satisfied"),
        }
        elig, ready = compute_scores(reqs, matches)
        assert 0 < elig < 100
        assert 0 < ready < 100

    def test_score_is_deterministic(self):
        from app.services.readiness_scorer import compute_scores
        reqs = [_req("eligibility"), _req("budget")]
        matches = {
            reqs[0].id: _match("satisfied"),
            reqs[1].id: _match("partially_satisfied"),
        }
        assert compute_scores(reqs, matches) == compute_scores(reqs, matches)

    def test_preferred_reqs_excluded_from_required_score(self):
        from app.services.readiness_scorer import compute_scores
        required = _req("eligibility", importance="required")
        preferred = _req("narrative", importance="preferred")
        matches = {
            required.id: _match("satisfied"),
            preferred.id: _match("not_satisfied"),
        }
        _, ready = compute_scores([required, preferred], matches)
        assert ready == 100

    def test_generate_risk_flags_high_for_required_not_satisfied(self):
        from app.services.readiness_scorer import generate_risk_flags
        req = _req("eligibility")
        match = _match("not_satisfied")
        flags = generate_risk_flags([req], {req.id: match})
        assert len(flags) == 1
        assert flags[0].severity == "high"

    def test_generate_risk_flags_medium_for_partial(self):
        from app.services.readiness_scorer import generate_risk_flags
        req = _req("budget")
        match = _match("partially_satisfied")
        flags = generate_risk_flags([req], {req.id: match})
        assert len(flags) == 1
        assert flags[0].severity == "medium"

    def test_generate_risk_flags_none_when_satisfied(self):
        from app.services.readiness_scorer import generate_risk_flags
        req = _req("eligibility")
        flags = generate_risk_flags([req], {req.id: _match("satisfied")})
        assert flags == []

    def test_generate_missing_documents(self):
        from app.services.readiness_scorer import generate_missing_documents
        req = _req("required_document")
        req.requirement_text = "Applicant must provide: IRS Determination Letter"
        match = _match("not_satisfied")
        missing = generate_missing_documents([req], {req.id: match})
        assert len(missing) == 1
        assert "IRS Determination Letter" in missing[0].name

    def test_no_missing_documents_when_satisfied(self):
        from app.services.readiness_scorer import generate_missing_documents
        req = _req("required_document")
        req.requirement_text = "Applicant must provide: Annual Report"
        missing = generate_missing_documents([req], {req.id: _match("satisfied")})
        assert missing == []


# ---------------------------------------------------------------------------
# Grant extractor (monkeypatched LLM at the USE SITE)
# ---------------------------------------------------------------------------

_EXTRACTION_6 = {
    "grant_name": "Community STEM Fund",
    "funder_name": "Ohio Foundation",
    "deadline": "May 2026",
    "eligibility_requirements": [
        {"text": "Applicant must be a 501(c)(3) nonprofit.", "required": True, "category": "eligibility", "source_quote": None},
        {"text": "Organization must serve youth in Ohio.", "required": True, "category": "eligibility", "source_quote": None},
    ],
    "required_documents": [
        {"document_name": "IRS determination letter", "required": True},
        {"document_name": "Board member list", "required": True},
    ],
    "narrative_questions": [
        {"question": "Describe your mission and primary programs.", "topic": "mission"},
    ],
    "budget_requirements": ["Grant request must not exceed 25% of annual budget."],
    "risk_flags": [],
}

_EXTRACTION_1 = {
    "eligibility_requirements": [
        {"text": "Must be a 501(c)(3) nonprofit.", "required": True, "category": "eligibility", "source_quote": None},
    ],
    "required_documents": [],
    "narrative_questions": [],
    "budget_requirements": [],
}


class TestGrantExtractor:
    def test_extract_requirements_saves_rows(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        db_session: Session,
        monkeypatch,
    ):
        import app.services.grant_extractor as ge
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: _EXTRACTION_6)

        _upload_pdf(
            client, org_id, project_id, "grant_opportunity", "grant.pdf",
            "Grant open to 501c3 nonprofits serving Ohio youth. IRS letter required. Deadline May 2026.",
        )

        from app.services.grant_extractor import extract_requirements
        reqs = extract_requirements(db_session, project_id)
        # 2 eligibility + 2 docs + 1 narrative + 1 budget = 6
        assert len(reqs) == 6

    def test_extract_requirements_correct_types(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        db_session: Session,
        monkeypatch,
    ):
        import app.services.grant_extractor as ge
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: _EXTRACTION_6)

        _upload_pdf(client, org_id, project_id, "grant_opportunity", "grant.pdf",
                    "Community STEM Fund is open to qualified nonprofit organizations serving Ohio youth.")

        from app.services.grant_extractor import extract_requirements
        reqs = extract_requirements(db_session, project_id)

        types = {r.requirement_type for r in reqs}
        assert "eligibility" in types
        assert "required_document" in types
        assert "narrative" in types
        assert "budget" in types

    def test_extract_requirements_no_grant_doc_raises(
        self, db_session: Session, project_id: str
    ):
        from app.services.grant_extractor import extract_requirements
        with pytest.raises(ValueError, match="No grant_opportunity document"):
            extract_requirements(db_session, project_id)

    def test_extract_requirements_empty_llm_response_produces_no_rows(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        db_session: Session,
        monkeypatch,
    ):
        import app.services.grant_extractor as ge
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: {})

        _upload_pdf(client, org_id, project_id, "grant_opportunity", "grant.pdf",
                    "Grant application requirements and eligibility criteria for nonprofit organizations.")

        from app.services.grant_extractor import extract_requirements
        reqs = extract_requirements(db_session, project_id)
        assert reqs == []


# ---------------------------------------------------------------------------
# Evidence matcher (monkeypatched LLM at the USE SITE)
# ---------------------------------------------------------------------------

_MATCH_RESPONSE = {
    "status": "satisfied",
    "confidence": 0.88,
    "explanation": "The document clearly states 501(c)(3) status.",
    "supporting_citations": [
        {"document_name": "Mission Statement.pdf", "page_number": 1, "summary": "Org is 501(c)(3)."}
    ],
    "missing_evidence": [],
}


class TestEvidenceMatcher:
    def test_match_requirement_persists_evidence_row(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        db_session: Session,
        monkeypatch,
    ):
        import app.services.evidence_matcher as em
        monkeypatch.setattr(em, "call_claude_json", lambda **kw: _MATCH_RESPONSE)

        _upload_pdf(
            client, org_id, project_id, "mission_statement", "mission.pdf",
            "BrightPath Youth Foundation is a registered 501(c)(3) nonprofit in Columbus Ohio.",
        )

        from app.services.embedding_service import embed_chunks_for_project
        embed_chunks_for_project(db_session, project_id)

        from app.models.analysis import EvidenceMatch, GrantRequirement
        req = GrantRequirement(
            id=f"req_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            requirement_type="eligibility",
            requirement_text="Applicant must be a registered 501(c)(3) nonprofit.",
            importance="required",
        )
        db_session.add(req)
        db_session.flush()

        from app.services.evidence_matcher import match_requirement
        ev, citations = match_requirement(db_session, req, project_id)

        persisted = (
            db_session.query(EvidenceMatch)
            .filter(EvidenceMatch.requirement_id == req.id)
            .first()
        )
        assert persisted is not None
        assert persisted.status == "satisfied"
        assert persisted.match_score == pytest.approx(0.88)
        assert len(citations) == 1

    def test_match_requirement_no_chunks_returns_not_satisfied(
        self, db_session: Session, project_id: str
    ):
        from app.models.analysis import GrantRequirement
        req = GrantRequirement(
            id=f"req_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            requirement_type="eligibility",
            requirement_text="Must serve low-income youth.",
            importance="required",
        )
        db_session.add(req)
        db_session.flush()

        from app.services.evidence_matcher import match_requirement
        ev, citations = match_requirement(db_session, req, project_id)

        assert ev.status == "not_satisfied"
        assert citations == []


# ---------------------------------------------------------------------------
# End-to-end analysis route tests
# ---------------------------------------------------------------------------

class TestAnalysisEndToEnd:
    def test_analyze_without_grant_doc_returns_mock_data(
        self, client: TestClient, project_id: str
    ):
        """Without a grant_opportunity document the pipeline falls back to BrightPath mock."""
        resp = client.post(f"/projects/{project_id}/analyze")
        assert resp.status_code == 200
        assert resp.json()["status"] == "analyzed"

        resp2 = client.get(f"/projects/{project_id}/analysis")
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["eligibility_score"] == 82
        assert body["readiness_score"] == 74
        assert len(body["requirements"]) == 10

    def test_analyze_without_api_key_falls_back_to_mock(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        monkeypatch,
    ):
        """Even with a grant doc, no API key → mock fallback."""
        from app.core.config import settings
        monkeypatch.setattr(settings, "anthropic_api_key", "")

        _upload_pdf(
            client, org_id, project_id, "grant_opportunity", "grant.pdf",
            "Grant for nonprofits. Eligibility: must be 501c3. IRS letter required.",
        )

        resp = client.post(f"/projects/{project_id}/analyze")
        assert resp.status_code == 200

        body = client.get(f"/projects/{project_id}/analysis").json()
        assert body["eligibility_score"] == 82

    def test_analyze_with_grant_doc_and_api_key_uses_real_pipeline(
        self,
        client: TestClient,
        org_id: str,
        project_id: str,
        monkeypatch,
    ):
        """With both a grant doc and API key (mocked), the real pipeline runs."""
        import app.services.grant_extractor as ge
        import app.services.evidence_matcher as em
        from app.core.config import settings

        monkeypatch.setattr(settings, "anthropic_api_key", "fake_key_for_test")
        monkeypatch.setattr(ge, "call_claude_json", lambda **kw: _EXTRACTION_1)
        monkeypatch.setattr(em, "call_claude_json", lambda **kw: _MATCH_RESPONSE)

        _upload_pdf(
            client, org_id, project_id, "mission_statement", "mission.pdf",
            "BrightPath is a 501(c)(3) nonprofit dedicated to STEM mentoring for youth in Columbus Ohio.",
        )
        _upload_pdf(
            client, org_id, project_id, "grant_opportunity", "grant.pdf",
            "Community STEM Fund: open to 501c3 nonprofits serving Ohio youth.",
        )

        resp = client.post(f"/projects/{project_id}/analyze")
        assert resp.status_code == 200

        body = client.get(f"/projects/{project_id}/analysis").json()
        assert body["project_id"] == project_id
        assert isinstance(body["eligibility_score"], int)
        assert 0 <= body["eligibility_score"] <= 100
        # _EXTRACTION_1 has exactly 1 eligibility requirement
        assert len(body["requirements"]) == 1
        assert body["requirements"][0]["status"] == "satisfied"

    def test_get_analysis_before_analyze_returns_404(
        self, client: TestClient, project_id: str
    ):
        resp = client.get(f"/projects/{project_id}/analysis")
        assert resp.status_code == 404

    def test_analysis_result_persisted_to_db(
        self, client: TestClient, project_id: str, db_session: Session
    ):
        from app.models.analysis import ReadinessReport
        client.post(f"/projects/{project_id}/analyze")
        report = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        assert report is not None
        assert report.eligibility_score == 82
        assert isinstance(report.requirements, list)
