"""
Integration tests for the upload + analyze project lifecycle.

Covers:
- Document upload updates document list
- Project status transitions through the lifecycle
- Analysis runs correctly after documents are uploaded
- Document ownership enforced during upload
- Full end-to-end: create project -> upload docs -> run analysis -> get analysis
"""
import io

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _make_pdf(text: str = "Grant program details for youth STEM education.") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _upload(
    client: TestClient,
    org_id: str,
    project_id: str,
    filename: str,
    doc_type: str = "annual_report",
    content: bytes | None = None,
) -> dict:
    if content is None:
        content = _make_pdf()
    resp = client.post(
        "/documents/upload",
        data={"organization_id": org_id, "project_id": project_id, "document_type": doc_type},
        files={"file": (filename, io.BytesIO(content), "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Document list after upload
# ---------------------------------------------------------------------------

def test_document_appears_in_list_after_upload(
    client: TestClient, org_id: str, project_id: str
) -> None:
    _upload(client, org_id, project_id, "mission.pdf", "mission_statement")
    docs = client.get(f"/projects/{project_id}/documents").json()
    assert any(d["filename"] == "mission.pdf" for d in docs)


def test_multiple_uploads_all_appear_in_list(
    client: TestClient, org_id: str, project_id: str
) -> None:
    _upload(client, org_id, project_id, "mission.pdf", "mission_statement")
    _upload(client, org_id, project_id, "budget.pdf", "budget")
    _upload(client, org_id, project_id, "grant.pdf", "grant_opportunity")

    docs = client.get(f"/projects/{project_id}/documents").json()
    filenames = {d["filename"] for d in docs}
    assert {"mission.pdf", "budget.pdf", "grant.pdf"} == filenames


def test_uploaded_pdf_status_is_parsed(
    client: TestClient, org_id: str, project_id: str
) -> None:
    doc = _upload(client, org_id, project_id, "program.pdf", "program_description",
                  content=_make_pdf("Detailed program description for grant application review."))
    assert doc["status"] == "parsed"


def test_uploaded_doc_has_correct_type(
    client: TestClient, org_id: str, project_id: str
) -> None:
    _upload(client, org_id, project_id, "grant_rfp.pdf", "grant_opportunity")
    docs = client.get(f"/projects/{project_id}/documents").json()
    grant_doc = next(d for d in docs if d["filename"] == "grant_rfp.pdf")
    assert grant_doc["document_type"] == "grant_opportunity"


def test_document_list_requires_auth(client: TestClient, project_id: str) -> None:
    saved = client.headers.get("authorization")
    del client.headers["authorization"]
    try:
        resp = client.get(f"/projects/{project_id}/documents")
        assert resp.status_code == 401
    finally:
        if saved:
            client.headers["Authorization"] = saved


def test_document_upload_requires_auth(
    client: TestClient, org_id: str, project_id: str
) -> None:
    saved = client.headers.get("authorization")
    del client.headers["authorization"]
    try:
        resp = client.post(
            "/documents/upload",
            data={"organization_id": org_id, "project_id": project_id, "document_type": "other"},
            files={"file": ("x.pdf", io.BytesIO(_make_pdf()), "application/pdf")},
        )
        assert resp.status_code == 401
    finally:
        if saved:
            client.headers["Authorization"] = saved


def test_upload_to_other_users_project_returns_403(client: TestClient) -> None:
    """User B cannot upload to User A's project."""
    # User A creates org + project
    _ORG = {"name": "A", "mission": "m", "location": "x", "nonprofit_type": "501(c)(3)",
             "annual_budget": 1, "population_served": "x"}
    org_a = client.post("/organizations", json=_ORG).json()["id"]
    proj_a = client.post("/projects", json={"organization_id": org_a, "grant_name": "G"}).json()["id"]

    # User B registers + tries to upload
    token_b = client.post("/auth/register",
                          json={"email": "uploader_b@test.com", "password": "pass12345"}).json()["access_token"]
    resp = client.post(
        "/documents/upload",
        data={"organization_id": org_a, "project_id": proj_a, "document_type": "other"},
        files={"file": ("x.pdf", io.BytesIO(_make_pdf()), "application/pdf")},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Project status transitions
# ---------------------------------------------------------------------------

def test_new_project_status_is_draft(client: TestClient, org_id: str, project_id: str) -> None:
    resp = client.get(f"/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


def test_project_status_becomes_analyzed_after_analysis(
    client: TestClient, org_id: str, project_id: str
) -> None:
    resp = client.post(f"/projects/{project_id}/analyze")
    assert resp.status_code == 200
    assert resp.json()["status"] == "analyzed"

    updated = client.get(f"/projects/{project_id}").json()
    assert updated["status"] == "analyzed"


# ---------------------------------------------------------------------------
# Full lifecycle: upload -> analyze -> get analysis
# ---------------------------------------------------------------------------

def test_full_lifecycle_upload_analyze_get_analysis(
    client: TestClient, org_id: str, project_id: str
) -> None:
    # 1. Upload mission statement
    _upload(client, org_id, project_id, "mission.pdf", "mission_statement",
            content=_make_pdf("BrightPath Youth Foundation provides STEM mentoring to Columbus youth."))

    # 2. Upload grant opportunity
    _upload(client, org_id, project_id, "grant.pdf", "grant_opportunity",
            content=_make_pdf("Community STEM Fund: applicants must be 501c3 nonprofits serving Ohio youth."))

    # 3. Verify documents are present
    docs = client.get(f"/projects/{project_id}/documents").json()
    assert len(docs) == 2

    # 4. Run analysis (uses mock fallback since no ANTHROPIC_API_KEY in tests)
    resp = client.post(f"/projects/{project_id}/analyze")
    assert resp.status_code == 200
    assert resp.json()["status"] == "analyzed"

    # 5. Get analysis results
    analysis = client.get(f"/projects/{project_id}/analysis").json()
    assert analysis["project_id"] == project_id
    assert isinstance(analysis["eligibility_score"], int)
    assert isinstance(analysis["readiness_score"], int)
    assert len(analysis["requirements"]) > 0
    assert "missing_documents" in analysis
    assert "risk_flags" in analysis
    assert "draft_answers" in analysis


def test_analysis_not_available_before_analyze(
    client: TestClient, project_id: str
) -> None:
    resp = client.get(f"/projects/{project_id}/analysis")
    assert resp.status_code == 404


def test_re_analysis_succeeds(client: TestClient, org_id: str, project_id: str) -> None:
    """Running analysis twice on the same project should succeed."""
    _upload(client, org_id, project_id, "mission.pdf", "mission_statement")

    r1 = client.post(f"/projects/{project_id}/analyze")
    assert r1.status_code == 200

    r2 = client.post(f"/projects/{project_id}/analyze")
    assert r2.status_code == 200


def test_document_page_count_populated_after_upload(
    client: TestClient, org_id: str, project_id: str
) -> None:
    """PDF uploads should have page_count set after parsing."""
    _upload(client, org_id, project_id, "report.pdf", "annual_report")
    docs = client.get(f"/projects/{project_id}/documents").json()
    doc = next(d for d in docs if d["filename"] == "report.pdf")
    assert doc["page_count"] == 1  # single-page test PDF


def test_demo_project_already_analyzed(client: TestClient) -> None:
    """The seeded BrightPath demo project should be accessible and analyzed."""
    # Login as demo user
    token = client.post("/auth/login",
                        json={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    proj = client.get("/projects/proj_stem_2026", headers=h).json()
    assert proj["status"] == "analyzed"

    analysis = client.get("/projects/proj_stem_2026/analysis", headers=h).json()
    assert analysis["eligibility_score"] == 82
    assert analysis["readiness_score"] == 74
