"""Document lifecycle: validation → persistence → storage → parsing → chunking → deletion."""
import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.document import DocumentType
from app.services import document_parser, storage_service

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILENAME_LENGTH = 255


def _doc_id() -> str:
    return f"doc_{uuid.uuid4().hex[:12]}"


def _chunk_id() -> str:
    return f"chunk_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_filename(filename: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    if len(filename) > MAX_FILENAME_LENGTH:
        return False, "Filename too long."
    suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        return False, (
            f"File type '{suffix}' not allowed. "
            f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return True, ""


# ---------------------------------------------------------------------------
# Core upload flow
# ---------------------------------------------------------------------------

def upload_document(
    db: Session,
    organization_id: str,
    project_id: str,
    document_type: DocumentType,
    filename: str,
    content: bytes,
) -> Document:
    """
    Full upload pipeline:
      1. Create Document record (status=uploaded)
      2. Persist file to local storage
      3. Parse PDF → create DocumentChunk records
      4. Update Document with page_count and final status
    Returns the committed Document.
    """
    doc_id = _doc_id()

    doc = Document(
        id=doc_id,
        organization_id=organization_id,
        project_id=project_id,
        document_type=document_type,
        filename=filename,
        status="uploaded",
    )
    db.add(doc)
    db.flush()

    # Persist file bytes
    storage_url = storage_service.save_file(content, project_id, doc_id, filename)
    doc.storage_url = storage_url
    doc.status = "stored"

    # Parse and chunk PDFs
    suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if suffix == ".pdf":
        file_path = storage_service.get_file_path(storage_url)
        try:
            pages = document_parser.parse_pdf(file_path)
            chunks = document_parser.chunk_pages(pages, doc_id, filename)
            for chunk in chunks:
                db.add(
                    DocumentChunk(
                        id=_chunk_id(),
                        document_id=chunk.document_id,
                        document_name=chunk.document_name,
                        page_number=chunk.page_number,
                        chunk_index=chunk.chunk_index,
                        chunk_text=chunk.chunk_text,
                    )
                )
            doc.page_count = max((p.page_number for p in pages), default=0) if pages else 0
            doc.status = "parsed"
        except ValueError:
            # Malformed or unreadable PDF — keep file stored, mark status accordingly
            doc.status = "parse_failed"

    db.flush()
    return doc


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_document(db: Session, doc_id: str) -> Document | None:
    return db.get(Document, doc_id)


def list_documents_for_project(db: Session, project_id: str) -> list[Document]:
    return db.query(Document).filter(Document.project_id == project_id).all()


def list_chunks_for_document(db: Session, doc_id: str) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


def list_chunks_for_project(db: Session, project_id: str) -> list[DocumentChunk]:
    """Returns all chunks across all documents in a project, ordered by doc then chunk_index."""
    return (
        db.query(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(Document.project_id == project_id)
        .order_by(Document.id, DocumentChunk.chunk_index)
        .all()
    )


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------

def delete_document(db: Session, doc_id: str) -> bool:
    """Delete a document, its chunks, and its file on disk.

    Returns True if the document was found and deleted, False if not found.
    File deletion errors are logged but do not abort the DB deletion.

    Deletion order (Postgres FK enforcement):
      EvidenceMatch (references document_chunk_id) →
      DocumentChunk (references document_id) →
      Document
    """
    from app.models.analysis import EvidenceMatch

    doc = db.get(Document, doc_id)
    if doc is None:
        return False

    # Collect chunk IDs so we can delete referencing EvidenceMatch rows first.
    # Postgres enforces evidence_matches.document_chunk_id FK strictly.
    chunk_ids = [
        row.id
        for row in db.query(DocumentChunk.id)
        .filter(DocumentChunk.document_id == doc_id)
        .all()
    ]
    if chunk_ids:
        db.query(EvidenceMatch).filter(
            EvidenceMatch.document_chunk_id.in_(chunk_ids)
        ).delete(synchronize_session="fetch")

    # Now safe to remove the chunks themselves
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete(
        synchronize_session="fetch"
    )

    # Remove file from local storage
    if doc.storage_url:
        try:
            file_path = storage_service.get_file_path(doc.storage_url)
            if file_path.exists():
                file_path.unlink()
        except Exception as exc:
            logger.warning("Could not remove file %s: %s", doc.storage_url, exc)

    db.delete(doc)
    db.flush()
    return True
