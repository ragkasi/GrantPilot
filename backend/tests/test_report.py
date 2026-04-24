"""
Phase 5 report generation tests.

Tests cover:
  - generate_pdf() returns valid PDF bytes
  - /report/download endpoint streams the PDF
  - report_pdf_url is persisted after first download
  - /report JSON endpoint returns a download URL after generation
  - Endpoint returns 404 before analysis runs
  - PDF content contains expected strings (verified via PyMuPDF)
  - Re-running analysis resets report_pdf_url (stale PDF cleared)
"""
import io
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_analysis(client: TestClient, project_id: str) -> None:
    resp = client.post(f"/projects/{project_id}/analyze")
    assert resp.status_code == 200


def _pdf_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = " ".join(page.get_text() for page in doc)
    doc.close()
    return text


# ---------------------------------------------------------------------------
# Unit tests — generate_pdf()
# ---------------------------------------------------------------------------

class TestGeneratePdf:
    def _make_report(self) -> object:
        from types import SimpleNamespace
        from app.models.analysis import ReadinessReport
        from app.models.organization import Organization
        from app.models.project import Project

        org = SimpleNamespace(
            id="org_test",
            name="BrightPath Youth Foundation",
            mission="Provide STEM mentoring.",
            location="Columbus, Ohio",
            nonprofit_type="501(c)(3)",
            annual_budget=420_000,
            population_served="Low-income youth",
        )
        project = SimpleNamespace(
            id="proj_test",
            organization_id="org_test",
            grant_name="Community STEM Access Fund",
            funder_name="Ohio Community Foundation",
            deadline="May 15, 2026",
            grant_source_url=None,
            grant_amount="$50,000 – $150,000",
            status="analyzed",
        )
        report = SimpleNamespace(
            id="report_test",
            project_id="proj_test",
            eligibility_score=82,
            readiness_score=74,
            requirements=[
                {
                    "id": "req_1",
                    "text": "Applicant must be a registered 501(c)(3) nonprofit.",
                    "type": "eligibility",
                    "importance": "required",
                    "status": "satisfied",
                    "confidence": 0.95,
                    "evidence": [
                        {
                            "document_name": "Mission Statement.pdf",
                            "page_number": 1,
                            "summary": "Organization is a 501(c)(3) incorporated in Ohio.",
                        }
                    ],
                },
                {
                    "id": "req_2",
                    "text": "Applicant must provide proof of IRS tax-exempt status.",
                    "type": "required_document",
                    "importance": "required",
                    "status": "not_satisfied",
                    "confidence": 0.0,
                    "evidence": [],
                },
            ],
            missing_items=[
                {
                    "name": "IRS Determination Letter",
                    "required": True,
                    "description": "Official IRS letter confirming tax-exempt status.",
                }
            ],
            risk_flags=[
                {
                    "severity": "high",
                    "title": "IRS determination letter not uploaded",
                    "description": "Hard eligibility requirement. Without it, application is disqualified.",
                }
            ],
            draft_answers=[
                {
                    "id": "draft_1",
                    "question": "Describe your organization mission.",
                    "draft_answer": "BrightPath Youth Foundation provides STEM mentoring to low-income youth in Columbus, Ohio.",
                    "citations": [
                        {"document_name": "Mission Statement.pdf", "page_number": 1, "summary": "States mission."}
                    ],
                    "missing_evidence": [],
                    "confidence": 0.91,
                }
            ],
            report_pdf_url=None,
        )
        return org, project, report

    def test_generate_pdf_returns_bytes(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000

    def test_generate_pdf_starts_with_pdf_header(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_pdf_is_parseable_by_pymupdf(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        assert doc.page_count >= 1
        doc.close()

    def test_generate_pdf_contains_org_name(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        text = _pdf_text(pdf_bytes)
        assert "BrightPath" in text

    def test_generate_pdf_contains_grant_name(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        text = _pdf_text(pdf_bytes)
        assert "STEM Access Fund" in text

    def test_generate_pdf_contains_scores(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        text = _pdf_text(pdf_bytes)
        assert "82" in text
        assert "74" in text

    def test_generate_pdf_contains_section_headers(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        text = _pdf_text(pdf_bytes)
        assert "Requirements" in text
        assert "Risk Flags" in text
        assert "Draft" in text

    def test_generate_pdf_contains_draft_answer_question(self):
        from app.services.report_generator import generate_pdf
        org, project, report = self._make_report()
        pdf_bytes = generate_pdf(project, org, report)
        text = _pdf_text(pdf_bytes)
        assert "mission" in text.lower()

    def test_generate_pdf_with_empty_sections_does_not_crash(self):
        from app.services.report_generator import generate_pdf
        from types import SimpleNamespace
        org, project, _ = self._make_report()
        empty_report = SimpleNamespace(
            id="r",
            project_id="p",
            eligibility_score=0,
            readiness_score=0,
            requirements=[],
            missing_items=[],
            risk_flags=[],
            draft_answers=[],
            report_pdf_url=None,
        )
        pdf_bytes = generate_pdf(project, org, empty_report)
        assert len(pdf_bytes) > 500


# ---------------------------------------------------------------------------
# HTTP endpoint tests
# ---------------------------------------------------------------------------

class TestReportEndpoint:
    def test_download_before_analysis_returns_404(
        self, client: TestClient, project_id: str
    ):
        resp = client.get(f"/projects/{project_id}/report/download")
        assert resp.status_code == 404

    def test_download_after_analysis_returns_pdf(
        self, client: TestClient, org_id: str, project_id: str
    ):
        _run_analysis(client, project_id)
        resp = client.get(f"/projects/{project_id}/report/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_download_returns_valid_pdf_content(
        self, client: TestClient, org_id: str, project_id: str
    ):
        _run_analysis(client, project_id)
        resp = client.get(f"/projects/{project_id}/report/download")
        text = _pdf_text(resp.content)
        assert "Grant Readiness Report" in text
        assert "Eligibility" in text

    def test_download_has_attachment_content_disposition(
        self, client: TestClient, project_id: str
    ):
        _run_analysis(client, project_id)
        resp = client.get(f"/projects/{project_id}/report/download")
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_report_url_persisted_after_download(
        self, client: TestClient, project_id: str, db_session: Session
    ):
        from app.models.analysis import ReadinessReport
        _run_analysis(client, project_id)
        client.get(f"/projects/{project_id}/report/download")

        report = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        assert report is not None
        assert report.report_pdf_url is not None

    def test_report_json_has_download_url_after_generation(
        self, client: TestClient, project_id: str
    ):
        _run_analysis(client, project_id)
        client.get(f"/projects/{project_id}/report/download")

        resp = client.get(f"/projects/{project_id}/report")
        assert resp.status_code == 200
        body = resp.json()
        assert body["report_pdf_url"] is not None
        assert "download" in body["report_pdf_url"]

    def test_report_json_url_is_null_before_download(
        self, client: TestClient, project_id: str
    ):
        _run_analysis(client, project_id)
        resp = client.get(f"/projects/{project_id}/report")
        assert resp.status_code == 200
        # No download triggered yet — URL is null
        body = resp.json()
        assert body["report_pdf_url"] is None

    def test_second_download_reuses_cached_pdf(
        self, client: TestClient, project_id: str, db_session: Session
    ):
        from app.models.analysis import ReadinessReport
        _run_analysis(client, project_id)
        client.get(f"/projects/{project_id}/report/download")

        first_url = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        ).report_pdf_url

        resp2 = client.get(f"/projects/{project_id}/report/download")
        assert resp2.status_code == 200

        second_url = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        ).report_pdf_url

        assert first_url == second_url  # same file reused

    def test_re_analysis_clears_report_url(
        self, client: TestClient, project_id: str, db_session: Session
    ):
        from app.models.analysis import ReadinessReport
        _run_analysis(client, project_id)
        client.get(f"/projects/{project_id}/report/download")

        # Verify URL is set
        report = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        assert report.report_pdf_url is not None

        # Re-run analysis
        _run_analysis(client, project_id)
        db_session.refresh(report)
        assert report.report_pdf_url is None  # cleared by re-analysis

    def test_download_unknown_project_returns_404(self, client: TestClient):
        resp = client.get("/projects/proj_ghost/report/download")
        assert resp.status_code == 404

    def test_generate_and_save_creates_file_on_disk(
        self, client: TestClient, project_id: str, db_session: Session, tmp_path
    ):
        _run_analysis(client, project_id)

        from app.services import report_generator
        storage_url = report_generator.generate_and_save(db_session, project_id)

        from app.services.storage_service import get_file_path
        pdf_path = get_file_path(storage_url)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 1000
