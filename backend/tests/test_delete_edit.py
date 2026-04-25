"""Tests for document deletion and project editing endpoints."""
import io

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _make_pdf(text: str = "Sample grant document text.") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _upload(
    client, org_id, project_id,
    filename="test.pdf", doc_type="annual_report", content: bytes | None = None
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
# Document deletion
# ---------------------------------------------------------------------------

class TestDocumentDeletion:
    def test_delete_document_returns_204(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        doc = _upload(client, org_id, project_id)
        resp = client.delete(f"/documents/{doc['id']}")
        assert resp.status_code == 204

    def test_deleted_document_not_in_list(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        doc = _upload(client, org_id, project_id)
        client.delete(f"/documents/{doc['id']}")
        docs = client.get(f"/projects/{project_id}/documents").json()
        assert not any(d["id"] == doc["id"] for d in docs)

    def test_delete_unknown_document_returns_404(
        self, client: TestClient
    ) -> None:
        resp = client.delete("/documents/doc_doesnotexist")
        assert resp.status_code == 404

    def test_delete_requires_auth(self, client: TestClient, org_id: str, project_id: str) -> None:
        doc = _upload(client, org_id, project_id)
        saved = client.headers.get("authorization")
        del client.headers["authorization"]
        try:
            resp = client.delete(f"/documents/{doc['id']}")
            assert resp.status_code == 401
        finally:
            if saved:
                client.headers["Authorization"] = saved

    def test_delete_other_users_document_returns_403(self, client: TestClient) -> None:
        # User A owns the project
        _ORG = {
            "name": "Del Org", "mission": "m.", "location": "x",
            "nonprofit_type": "501(c)(3)", "annual_budget": 1, "population_served": "x",
        }
        org_a = client.post("/organizations", json=_ORG).json()["id"]
        proj_a = client.post(
            "/projects", json={"organization_id": org_a, "grant_name": "Grant A"}
        ).json()["id"]
        doc = _upload(client, org_a, proj_a)

        # User B tries to delete it
        token_b = client.post(
            "/auth/register", json={"email": "del_b@test.com", "password": "password123"}
        ).json()["access_token"]
        resp = client.delete(
            f"/documents/{doc['id']}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 403

    def test_delete_only_removes_target_document(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        doc1 = _upload(client, org_id, project_id, "keep.pdf")
        doc2 = _upload(client, org_id, project_id, "remove.pdf")

        client.delete(f"/documents/{doc2['id']}")

        docs = client.get(f"/projects/{project_id}/documents").json()
        ids = [d["id"] for d in docs]
        assert doc1["id"] in ids
        assert doc2["id"] not in ids

    def test_delete_removes_chunks_from_db(
        self, client: TestClient, org_id: str, project_id: str, db_session: Session
    ) -> None:
        from app.models.chunk import DocumentChunk
        doc = _upload(client, org_id, project_id, content=_make_pdf(
            "BrightPath Youth Foundation provides STEM mentoring to low-income youth in Ohio."
        ))
        doc_id = doc["id"]

        # Chunks should exist after upload
        chunks_before = db_session.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_id
        ).count()
        assert chunks_before >= 1

        client.delete(f"/documents/{doc_id}")

        chunks_after = db_session.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_id
        ).count()
        assert chunks_after == 0


# ---------------------------------------------------------------------------
# Project editing
# ---------------------------------------------------------------------------

class TestProjectEditing:
    def test_patch_grant_name(
        self, client: TestClient, project_id: str
    ) -> None:
        resp = client.patch(f"/projects/{project_id}", json={"grant_name": "Updated Grant Name"})
        assert resp.status_code == 200
        assert resp.json()["grant_name"] == "Updated Grant Name"

    def test_patch_funder_name(
        self, client: TestClient, project_id: str
    ) -> None:
        resp = client.patch(f"/projects/{project_id}", json={"funder_name": "New Foundation"})
        assert resp.status_code == 200
        assert resp.json()["funder_name"] == "New Foundation"

    def test_patch_deadline_and_amount(
        self, client: TestClient, project_id: str
    ) -> None:
        resp = client.patch(
            f"/projects/{project_id}",
            json={"deadline": "June 1, 2027", "grant_amount": "$75,000"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["deadline"] == "June 1, 2027"
        assert body["grant_amount"] == "$75,000"

    def test_patch_partial_only_updates_sent_fields(
        self, client: TestClient, project_id: str
    ) -> None:
        # Set up initial values
        client.patch(
            f"/projects/{project_id}",
            json={"funder_name": "Initial Funder", "deadline": "Jan 2027"},
        )
        # Now only update grant_name
        resp = client.patch(f"/projects/{project_id}", json={"grant_name": "Only This Changed"})
        body = resp.json()
        assert body["grant_name"] == "Only This Changed"
        assert body["funder_name"] == "Initial Funder"  # unchanged
        assert body["deadline"] == "Jan 2027"  # unchanged

    def test_patch_preserves_status(
        self, client: TestClient, project_id: str
    ) -> None:
        resp = client.patch(f"/projects/{project_id}", json={"grant_name": "Edited"})
        # Status should still be draft after a metadata edit
        assert resp.json()["status"] == "draft"

    def test_patch_empty_body_is_noop(
        self, client: TestClient, project_id: str
    ) -> None:
        before = client.get(f"/projects/{project_id}").json()
        resp = client.patch(f"/projects/{project_id}", json={})
        assert resp.status_code == 200
        after = resp.json()
        assert after["grant_name"] == before["grant_name"]

    def test_patch_requires_auth(self, client: TestClient, project_id: str) -> None:
        saved = client.headers.get("authorization")
        del client.headers["authorization"]
        try:
            resp = client.patch(f"/projects/{project_id}", json={"grant_name": "Hack"})
            assert resp.status_code == 401
        finally:
            if saved:
                client.headers["Authorization"] = saved

    def test_patch_other_users_project_returns_403(self, client: TestClient) -> None:
        _ORG = {
            "name": "Edit Org", "mission": "m.", "location": "x",
            "nonprofit_type": "501(c)(3)", "annual_budget": 1, "population_served": "x",
        }
        org_a = client.post("/organizations", json=_ORG).json()["id"]
        proj_a = client.post(
            "/projects", json={"organization_id": org_a, "grant_name": "A Grant"}
        ).json()["id"]

        token_b = client.post(
            "/auth/register", json={"email": "edit_b@test.com", "password": "password123"}
        ).json()["access_token"]
        resp = client.patch(
            f"/projects/{proj_a}",
            json={"grant_name": "Stolen"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 403

    def test_patch_grant_name_empty_rejected(
        self, client: TestClient, project_id: str
    ) -> None:
        resp = client.patch(f"/projects/{project_id}", json={"grant_name": ""})
        assert resp.status_code == 422

    def test_patch_does_not_reset_analysis(
        self, client: TestClient, org_id: str, project_id: str
    ) -> None:
        """Editing project metadata should not wipe existing analysis results."""
        client.post(f"/projects/{project_id}/analyze")
        client.patch(f"/projects/{project_id}", json={"funder_name": "New Funder"})
        analysis = client.get(f"/projects/{project_id}/analysis")
        assert analysis.status_code == 200
        assert analysis.json()["eligibility_score"] == 82
