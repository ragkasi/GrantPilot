from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import require_project_access
from app.core.database import get_db
from app.models.user import User
from app.schemas.analysis import AnalysisResponse, AnalyzeResponse, ReportResponse
from app.services import analysis_service, report_generator, storage_service

router = APIRouter(tags=["analysis"])


@router.post("/projects/{project_id}/analyze", response_model=AnalyzeResponse)
def analyze_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    from app.services import project_service
    require_project_access(db, project_id, current_user)
    project_service.update_project_status(db, project_id, "analyzing")
    analysis_service.run_analysis(project_id, db)
    project_service.update_project_status(db, project_id, "analyzed")
    return AnalyzeResponse(project_id=project_id, status="analyzed")


@router.get("/projects/{project_id}/analysis", response_model=AnalysisResponse)
def get_analysis(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    require_project_access(db, project_id, current_user)
    report = analysis_service.get_analysis(project_id, db)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run POST /projects/{project_id}/analyze first.",
        )
    return analysis_service.build_analysis_response(report)


@router.get("/projects/{project_id}/report", response_model=ReportResponse)
def get_report_metadata(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    require_project_access(db, project_id, current_user)
    report = analysis_service.get_analysis(project_id, db)
    pdf_url = report.report_pdf_url if report else None
    download_url = f"/projects/{project_id}/report/download" if pdf_url else None
    return ReportResponse(project_id=project_id, report_pdf_url=download_url)


@router.get("/projects/{project_id}/report/download")
def download_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    require_project_access(db, project_id, current_user)
    report = analysis_service.get_analysis(project_id, db)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="No analysis found. Run POST /projects/{project_id}/analyze first.",
        )

    if report.report_pdf_url:
        pdf_path = storage_service.get_file_path(report.report_pdf_url)
        if not pdf_path.exists():
            report.report_pdf_url = None

    if not report.report_pdf_url:
        try:
            report_generator.generate_and_save(db, project_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    pdf_path = storage_service.get_file_path(report.report_pdf_url)
    if not pdf_path.exists():
        raise HTTPException(status_code=500, detail="Report file could not be found after generation.")

    filename = f"grant_readiness_report_{project_id[:8]}.pdf"
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
