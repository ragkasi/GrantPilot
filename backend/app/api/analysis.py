from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analysis import AnalysisResponse, AnalyzeResponse, ReportResponse
from app.services import analysis_service, project_service

router = APIRouter(tags=["analysis"])


@router.post("/projects/{project_id}/analyze", response_model=AnalyzeResponse)
def analyze_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    record = project_service.get_project(db, project_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    project_service.update_project_status(db, project_id, "analyzing")
    analysis_service.run_analysis(project_id, db)
    project_service.update_project_status(db, project_id, "analyzed")

    return AnalyzeResponse(project_id=project_id, status="analyzed")


@router.get("/projects/{project_id}/analysis", response_model=AnalysisResponse)
def get_analysis(
    project_id: str,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    report = analysis_service.get_analysis(project_id, db)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run POST /projects/{project_id}/analyze first.",
        )
    return analysis_service.build_analysis_response(report)


@router.get("/projects/{project_id}/report", response_model=ReportResponse)
def get_report(
    project_id: str,
    db: Session = Depends(get_db),
) -> ReportResponse:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    report = analysis_service.get_analysis(project_id, db)
    pdf_url = report.report_pdf_url if report else None
    return ReportResponse(project_id=project_id, report_pdf_url=pdf_url)
