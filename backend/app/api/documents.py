from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_project_access
from app.core.database import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentSummary, DocumentType
from app.services import document_service

router = APIRouter(tags=["documents"])

_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/documents/upload", response_model=DocumentSummary, status_code=201)
async def upload_document(
    organization_id: str = Form(...),
    project_id: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentSummary:
    require_project_access(db, project_id, current_user)

    filename = file.filename or "upload"
    valid, err = document_service.validate_filename(filename)
    if not valid:
        raise HTTPException(status_code=422, detail=err)

    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 20 MB limit.")

    doc = document_service.upload_document(
        db=db,
        organization_id=organization_id,
        project_id=project_id,
        document_type=document_type,
        filename=filename,
        content=content,
    )
    return DocumentSummary(
        id=doc.id,
        filename=doc.filename,
        document_type=doc.document_type,
        status=doc.status,
    )


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a document and its associated chunks and file.

    Ownership is enforced through document → project → organization → user.
    """
    doc = document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Verify the caller owns the project this document belongs to
    require_project_access(db, doc.project_id, current_user)

    document_service.delete_document(db, doc_id)
    return Response(status_code=204)


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
def list_project_documents(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentResponse]:
    require_project_access(db, project_id, current_user)
    records = document_service.list_documents_for_project(db, project_id)
    return [
        DocumentResponse(
            id=r.id,
            organization_id=r.organization_id,
            project_id=r.project_id,
            filename=r.filename,
            document_type=r.document_type,
            status=r.status,
            page_count=r.page_count,
            created_at=r.created_at,
        )
        for r in records
    ]
