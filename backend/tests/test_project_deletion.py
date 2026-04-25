"""Tests for project deletion endpoint and cascade behavior."""
import io
import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _make_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Sample grant document text for deletion cascade tests with sufficient length.")
    data = doc.tobytes()
    doc.close()
    return data


def _upload(client, org_id, project_id):
    return client.post(
        "/documents/upload",
        data={"organization_id": org_id, "project_id": project_id, "document_type": "annual_report"},
        files={"file": ("report.pdf", io.BytesIO(_make_pdf()), "application/pdf")},
    )


class TestProjectDeletion:
    def test_delete_project_returns_204(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        resp = client.delete(f"/projects/{project_id}")
        assert resp.status_code == 204

    def test_deleted_project_not_in_list(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        client.delete(f"/projects/{project_id}")
        projects = client.get("/projects").json()
        assert not any(p["id"] == project_id for p in projects)

    def test_get_deleted_project_returns_404(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        client.delete(f"/projects/{project_id}")
        resp = client.get(f"/projects/{project_id}")
        assert resp.status_code == 404

    def test_delete_unknown_project_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/projects/proj_ghost")
        assert resp.status_code == 404

    def test_delete_requires_auth(
        self, client: TestClient, project_id: str
    ) -> None:
        saved = client.headers.get("authorization")
        del client.headers["authorization"]
        try:
            resp = client.delete(f"/projects/{project_id}")
            assert resp.status_code == 401
        finally:
            if saved:
                client.headers["Authorization"] = saved

    def test_delete_other_users_project_returns_403(self, client: TestClient) -> None:
        _ORG = {
            "name": "Other Org", "mission": "m.", "location": "x",
            "nonprofit_type": "501(c)(3)", "annual_budget": 1, "population_served": "x",
        }
        org_a = client.post("/organizations", json=_ORG).json()["id"]
        proj_a = client.post(
            "/projects", json={"organization_id": org_a, "grant_name": "A Grant"}
        ).json()["id"]

        token_b = client.post(
            "/auth/register", json={"email": "del_proj_b@test.com", "password": "password123"}
        ).json()["access_token"]
        resp = client.delete(
            f"/projects/{proj_a}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 403

    def test_delete_cascades_documents(
        self, client: TestClient, org_id: str, project_id: str, db_session: Session
    ) -> None:
        from app.models.document import Document
        _upload(client, org_id, project_id)
        # Ensure document exists
        docs_before = db_session.query(Document).filter(Document.project_id == project_id).count()
        assert docs_before == 1

        client.delete(f"/projects/{project_id}")

        docs_after = db_session.query(Document).filter(Document.project_id == project_id).count()
        assert docs_after == 0

    def test_delete_cascades_chunks(
        self, client: TestClient, org_id: str, project_id: str, db_session: Session
    ) -> None:
        from app.models.chunk import DocumentChunk
        from app.models.document import Document
        _upload(client, org_id, project_id)

        chunks_before = (
            db_session.query(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.project_id == project_id)
            .count()
        )
        assert chunks_before >= 1

        client.delete(f"/projects/{project_id}")

        chunks_after = (
            db_session.query(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.project_id == project_id)
            .count()
        )
        assert chunks_after == 0

    def test_delete_cascades_analysis(
        self, client: TestClient, org_id: str, project_id: str, db_session: Session
    ) -> None:
        from app.models.analysis import ReadinessReport
        # Run analysis so a ReadinessReport exists
        client.post(f"/projects/{project_id}/analyze")
        report_before = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        assert report_before is not None

        client.delete(f"/projects/{project_id}")

        report_after = (
            db_session.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        assert report_after is None

    def test_delete_demo_project_not_allowed_for_non_owner(
        self, client: TestClient
    ) -> None:
        """Test user cannot delete the seeded demo project."""
        # The client fixture creates a test user (not demo user)
        resp = client.delete("/projects/proj_stem_2026")
        assert resp.status_code == 403
