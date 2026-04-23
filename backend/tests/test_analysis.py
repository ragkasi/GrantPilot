from fastapi.testclient import TestClient


def test_analyze_returns_analyzed_status(client: TestClient, project_id: str) -> None:
    resp = client.post(f"/projects/{project_id}/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == project_id
    assert body["status"] == "analyzed"


def test_analyze_unknown_project_returns_404(client: TestClient) -> None:
    resp = client.post("/projects/proj_ghost/analyze")
    assert resp.status_code == 404


def test_get_analysis_after_analyze(client: TestClient, project_id: str) -> None:
    client.post(f"/projects/{project_id}/analyze")
    resp = client.get(f"/projects/{project_id}/analysis")
    assert resp.status_code == 200
    body = resp.json()

    assert body["project_id"] == project_id
    assert body["eligibility_score"] == 82
    assert body["readiness_score"] == 74
    assert len(body["requirements"]) == 10
    assert len(body["missing_documents"]) == 3
    assert len(body["risk_flags"]) == 4
    assert len(body["draft_answers"]) == 3


def test_get_analysis_before_analyze_returns_404(client: TestClient, project_id: str) -> None:
    resp = client.get(f"/projects/{project_id}/analysis")
    assert resp.status_code == 404


def test_get_analysis_unknown_project_returns_404(client: TestClient) -> None:
    resp = client.get("/projects/proj_ghost/analysis")
    assert resp.status_code == 404


def test_analysis_requirement_structure(client: TestClient, project_id: str) -> None:
    client.post(f"/projects/{project_id}/analyze")
    body = client.get(f"/projects/{project_id}/analysis").json()
    req = body["requirements"][0]
    assert "id" in req
    assert "text" in req
    assert "type" in req
    assert "importance" in req
    assert "status" in req
    assert "confidence" in req
    assert "evidence" in req


def test_analysis_draft_answer_has_citations(client: TestClient, project_id: str) -> None:
    client.post(f"/projects/{project_id}/analyze")
    body = client.get(f"/projects/{project_id}/analysis").json()
    draft = body["draft_answers"][0]
    assert len(draft["citations"]) > 0
    citation = draft["citations"][0]
    assert "document_name" in citation
    assert "page_number" in citation
    assert "summary" in citation


def test_get_report_before_analyze(client: TestClient, project_id: str) -> None:
    resp = client.get(f"/projects/{project_id}/report")
    assert resp.status_code == 200
    assert resp.json()["report_pdf_url"] is None


def test_get_report_after_analyze(client: TestClient, project_id: str) -> None:
    client.post(f"/projects/{project_id}/analyze")
    resp = client.get(f"/projects/{project_id}/report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == project_id
    # PDF generation is Phase 5; url is None for now
    assert body["report_pdf_url"] is None


def test_project_status_updated_after_analyze(client: TestClient, org_id: str, project_id: str) -> None:
    before = client.get(f"/projects/{project_id}").json()
    assert before["status"] == "draft"

    client.post(f"/projects/{project_id}/analyze")

    after = client.get(f"/projects/{project_id}").json()
    assert after["status"] == "analyzed"
