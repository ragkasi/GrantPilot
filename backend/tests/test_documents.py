"""HTTP-level document upload and listing tests."""
import io

import fitz  # PyMuPDF — used to create real test PDFs
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf(text: str = "Hello, grant world.") -> bytes:
    """Creates a minimal single-page PDF with the given text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _upload(
    client: TestClient,
    project_id: str,
    org_id: str,
    filename: str = "report.pdf",
    content: bytes | None = None,
    doc_type: str = "annual_report",
) -> object:
    if content is None:
        content = _make_pdf()
    return client.post(
        "/documents/upload",
        data={
            "organization_id": org_id,
            "project_id": project_id,
            "document_type": doc_type,
        },
        files={"file": (filename, io.BytesIO(content), "application/pdf")},
    )


# ---------------------------------------------------------------------------
# Upload tests
# ---------------------------------------------------------------------------

def test_upload_valid_pdf_returns_201(client: TestClient, org_id: str, project_id: str) -> None:
    resp = _upload(client, project_id, org_id)
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "report.pdf"
    assert body["document_type"] == "annual_report"
    assert body["id"].startswith("doc_")
    # A valid PDF should be parsed
    assert body["status"] == "parsed"


def test_upload_sets_page_count(client: TestClient, org_id: str, project_id: str) -> None:
    resp = _upload(client, project_id, org_id)
    assert resp.status_code == 201
    doc_id = resp.json()["id"]

    docs = client.get(f"/projects/{project_id}/documents").json()
    doc = next(d for d in docs if d["id"] == doc_id)
    assert doc["page_count"] == 1  # single-page test PDF


def test_upload_unknown_project_returns_404(client: TestClient, org_id: str) -> None:
    resp = _upload(client, "proj_ghost", org_id)
    assert resp.status_code == 404


def test_upload_disallowed_extension_returns_422(
    client: TestClient, org_id: str, project_id: str
) -> None:
    resp = _upload(client, project_id, org_id, filename="script.exe")
    assert resp.status_code == 422


def test_upload_invalid_pdf_bytes_marks_parse_failed(
    client: TestClient, org_id: str, project_id: str
) -> None:
    """A file with a .pdf extension but corrupt bytes should be stored but marked parse_failed."""
    resp = client.post(
        "/documents/upload",
        data={
            "organization_id": org_id,
            "project_id": project_id,
            "document_type": "annual_report",
        },
        files={"file": ("corrupt.pdf", io.BytesIO(b"this is not a pdf"), "application/pdf")},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "parse_failed"


def test_upload_non_pdf_stored_not_parsed(
    client: TestClient, org_id: str, project_id: str
) -> None:
    """A .txt file should be stored but not parsed (no chunks created by current pipeline)."""
    resp = client.post(
        "/documents/upload",
        data={
            "organization_id": org_id,
            "project_id": project_id,
            "document_type": "mission_statement",
        },
        files={"file": ("mission.txt", io.BytesIO(b"Our mission is to serve."), "text/plain")},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "stored"


# ---------------------------------------------------------------------------
# List documents
# ---------------------------------------------------------------------------

def test_list_project_documents(client: TestClient, org_id: str, project_id: str) -> None:
    _upload(client, project_id, org_id, "mission.pdf")
    _upload(client, project_id, org_id, "budget.pdf")

    resp = client.get(f"/projects/{project_id}/documents")
    assert resp.status_code == 200
    docs = resp.json()
    filenames = [d["filename"] for d in docs]
    assert "mission.pdf" in filenames
    assert "budget.pdf" in filenames


def test_list_documents_unknown_project_returns_404(client: TestClient) -> None:
    resp = client.get("/projects/proj_ghost/documents")
    assert resp.status_code == 404


def test_uploaded_pdf_creates_chunks(
    client: TestClient, org_id: str, project_id: str, db_session
) -> None:
    """After uploading a real PDF, DocumentChunk rows should exist in the DB."""
    from app.models.chunk import DocumentChunk
    from app.models.document import Document

    _upload(
        client, project_id, org_id, "program.pdf",
        content=_make_pdf(
            "BrightPath STEM Mentoring Program provides after-school support for low-income "
            "middle school students in Columbus, Ohio."
        ),
    )

    docs = db_session.query(Document).filter(Document.project_id == project_id).all()
    assert len(docs) == 1
    doc = docs[0]

    chunks = (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc.id)
        .all()
    )
    assert len(chunks) >= 1
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert len(chunks[0].chunk_text) >= 5
    assert chunks[0].document_name == "program.pdf"
