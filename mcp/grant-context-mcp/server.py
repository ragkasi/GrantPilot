"""
grant-context-mcp

MCP server that exposes GrantPilot's grant-analysis capabilities as
structured tools for Claude agents. All tools operate on project and
requirement IDs validated against the database -- no file paths, no shell
commands, no secrets in outputs.

Tool surface:
  parse_grant_requirements   -- return extracted requirements for a project
  extract_nonprofit_profile  -- return org + doc inventory for a project
  match_requirement_to_evidence -- run evidence matching for one requirement
  generate_readiness_checklist  -- return scores, flags, and missing docs
  generate_packet               -- generate/return the PDF report path

Security model (enforced in this file, not by callers):
  - All IDs validated against DB before any service call
  - Storage URLs are relative paths only (no absolute paths in output)
  - Environment variables never returned in any response
  - No shell execution; no arbitrary file access
  - Document content treated as data, not instructions
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap: add backend/ so we can import app.*
# This file lives at mcp/grant-context-mcp/server.py
# Backend is at  ../../backend/
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import json
import logging
import re

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="grant-context-mcp",
    instructions=(
        "Tools for analysing grant eligibility and readiness from uploaded nonprofit "
        "documents. Always pass a valid project_id. Never fabricate IDs. "
        "All outputs are grounded in uploaded documents; do not invent nonprofit facts."
    ),
)

# ---------------------------------------------------------------------------
# ID validation helpers
# ---------------------------------------------------------------------------

_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{3,60}$")


def _validate_id(value: str, label: str) -> str:
    """Raise ValueError if value looks unsafe (path traversal, shell injection, etc.)."""
    if not value or not _ID_PATTERN.match(value):
        raise ValueError(
            f"Invalid {label}: {value!r}. Must be 3-60 alphanumeric/underscore/hyphen chars."
        )
    return value


def _get_db():
    """Return a new SQLAlchemy session using the backend's engine."""
    from app.core.database import SessionLocal
    return SessionLocal()


# ---------------------------------------------------------------------------
# Tool: parse_grant_requirements
# ---------------------------------------------------------------------------

@mcp.tool()
def parse_grant_requirements(project_id: str) -> str:
    """
    Return the grant requirements already extracted for a project.

    If requirements have been extracted (after running /analyze), returns
    structured JSON. If none exist, returns an empty list with a hint.

    Input:
      project_id  --  ID of the GrantPilot project

    Output JSON:
    {
      "project_id": "...",
      "requirement_count": 3,
      "requirements": [
        {
          "id": "req_xxx",
          "text": "Applicant must be a registered 501(c)(3) nonprofit.",
          "type": "eligibility",
          "importance": "required"
        }
      ],
      "hint": "Run POST /projects/{id}/analyze to populate requirements."
    }
    """
    _validate_id(project_id, "project_id")
    db = _get_db()
    try:
        from app.models.analysis import GrantRequirement
        from app.models.project import Project

        project = db.get(Project, project_id)
        if project is None:
            return _err(f"Project '{project_id}' not found.")

        requirements = (
            db.query(GrantRequirement)
            .filter(GrantRequirement.project_id == project_id)
            .all()
        )

        hint = "" if requirements else (
            "No requirements found. Run POST /projects/{id}/analyze to extract requirements."
        )

        return json.dumps({
            "project_id": project_id,
            "grant_name": project.grant_name,
            "requirement_count": len(requirements),
            "requirements": [
                {
                    "id": r.id,
                    "text": r.requirement_text,
                    "type": r.requirement_type,
                    "importance": r.importance,
                }
                for r in requirements
            ],
            "hint": hint,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool: extract_nonprofit_profile
# ---------------------------------------------------------------------------

@mcp.tool()
def extract_nonprofit_profile(project_id: str) -> str:
    """
    Return the nonprofit profile and document inventory for a project.

    Combines organization metadata with the list of uploaded document types
    and their parse status, giving an agent a complete picture of what
    evidence is available.

    Input:
      project_id  --  ID of the GrantPilot project

    Output JSON:
    {
      "project_id": "...",
      "organization": {
        "id": "...", "name": "...", "mission": "...",
        "location": "...", "nonprofit_type": "...",
        "annual_budget": 420000, "population_served": "..."
      },
      "project": {
        "grant_name": "...", "funder_name": "...", "deadline": "...",
        "status": "analyzed"
      },
      "documents": [
        {"id": "doc_xxx", "filename": "mission.pdf", "type": "mission_statement",
         "status": "parsed", "page_count": 2}
      ],
      "document_type_summary": {"mission_statement": 1, "annual_report": 1}
    }
    """
    _validate_id(project_id, "project_id")
    db = _get_db()
    try:
        from app.models.document import Document
        from app.models.organization import Organization
        from app.models.project import Project

        project = db.get(Project, project_id)
        if project is None:
            return _err(f"Project '{project_id}' not found.")

        org = db.get(Organization, project.organization_id)
        if org is None:
            return _err(f"Organization for project '{project_id}' not found.")

        documents = (
            db.query(Document)
            .filter(Document.project_id == project_id)
            .order_by(Document.created_at)
            .all()
        )

        type_summary: dict[str, int] = {}
        for doc in documents:
            type_summary[doc.document_type] = type_summary.get(doc.document_type, 0) + 1

        return json.dumps({
            "project_id": project_id,
            "organization": {
                "id": org.id,
                "name": org.name,
                "mission": org.mission,
                "location": org.location,
                "nonprofit_type": org.nonprofit_type,
                "annual_budget": org.annual_budget,
                "population_served": org.population_served,
            },
            "project": {
                "grant_name": project.grant_name,
                "funder_name": project.funder_name,
                "deadline": project.deadline,
                "grant_amount": project.grant_amount,
                "status": project.status,
            },
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "type": doc.document_type,
                    "status": doc.status,
                    "page_count": doc.page_count,
                }
                for doc in documents
            ],
            "document_type_summary": type_summary,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool: match_requirement_to_evidence
# ---------------------------------------------------------------------------

@mcp.tool()
def match_requirement_to_evidence(project_id: str, requirement_id: str) -> str:
    """
    Retrieve or compute the evidence match for a single grant requirement.

    First checks for an existing EvidenceMatch row. If none exists, runs
    the evidence matcher live (requires ANTHROPIC_API_KEY). Falls back to
    keyword-based retrieval without LLM evaluation if no API key is set.

    Input:
      project_id       --  ID of the GrantPilot project
      requirement_id   --  ID of the GrantRequirement (from parse_grant_requirements)

    Output JSON:
    {
      "requirement_id": "req_xxx",
      "requirement_text": "...",
      "status": "satisfied | partially_satisfied | not_satisfied | unclear",
      "confidence": 0.88,
      "explanation": "...",
      "citations": [
        {"document_name": "...", "page_number": 1, "summary": "..."}
      ],
      "missing_evidence": []
    }
    """
    _validate_id(project_id, "project_id")
    _validate_id(requirement_id, "requirement_id")
    db = _get_db()
    try:
        from app.models.analysis import EvidenceMatch, GrantRequirement
        from app.models.project import Project

        project = db.get(Project, project_id)
        if project is None:
            return _err(f"Project '{project_id}' not found.")

        req = db.get(GrantRequirement, requirement_id)
        if req is None or req.project_id != project_id:
            return _err(
                f"Requirement '{requirement_id}' not found in project '{project_id}'."
            )

        # Check for existing persisted match
        existing = (
            db.query(EvidenceMatch)
            .filter(EvidenceMatch.requirement_id == requirement_id)
            .first()
        )

        if existing:
            # Return cached result — fetch the linked chunk for citations
            from app.models.chunk import DocumentChunk
            citations = []
            if existing.document_chunk_id:
                chunk = db.get(DocumentChunk, existing.document_chunk_id)
                if chunk:
                    citations.append({
                        "document_name": chunk.document_name,
                        "page_number": chunk.page_number,
                        "summary": chunk.chunk_text[:200],
                    })
            return json.dumps({
                "requirement_id": requirement_id,
                "requirement_text": req.requirement_text,
                "status": existing.status,
                "confidence": round(existing.match_score, 4),
                "explanation": existing.explanation,
                "citations": citations,
                "missing_evidence": [],
                "source": "cached",
            })

        # No cached match — run live matching
        from app.core.config import settings
        from app.services import evidence_matcher
        from app.services.embedding_service import embed_chunks_for_project

        # Ensure chunks are embedded first
        embed_chunks_for_project(db, project_id)

        ev, citations = evidence_matcher.match_requirement(db, req, project_id)
        db.commit()

        return json.dumps({
            "requirement_id": requirement_id,
            "requirement_text": req.requirement_text,
            "status": ev.status,
            "confidence": round(ev.match_score, 4),
            "explanation": ev.explanation,
            "citations": [c.model_dump() for c in citations],
            "missing_evidence": [],
            "source": "live",
        })
    except Exception as exc:
        logger.error("match_requirement_to_evidence failed: %s", exc)
        return _err(str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool: generate_readiness_checklist
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_readiness_checklist(project_id: str) -> str:
    """
    Return the grant readiness checklist for a project.

    Reads the stored ReadinessReport and returns a structured summary
    including scores, missing documents, risk flags, and per-requirement
    statuses. Analysis must have been run first.

    Input:
      project_id  --  ID of the GrantPilot project

    Output JSON:
    {
      "project_id": "...",
      "grant_name": "...",
      "eligibility_score": 82,
      "readiness_score": 74,
      "requirements_summary": {
        "total": 10, "satisfied": 7, "partial": 1, "not_met": 2
      },
      "missing_documents": [
        {"name": "IRS Determination Letter", "required": true, "description": "..."}
      ],
      "risk_flags": [
        {"severity": "high", "title": "...", "description": "..."}
      ],
      "requirements": [
        {"id": "...", "text": "...", "type": "...", "status": "...", "confidence": 0.9}
      ]
    }
    """
    _validate_id(project_id, "project_id")
    db = _get_db()
    try:
        from app.models.analysis import ReadinessReport
        from app.models.project import Project

        project = db.get(Project, project_id)
        if project is None:
            return _err(f"Project '{project_id}' not found.")

        report = (
            db.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        if report is None:
            return _err(
                f"No analysis found for project '{project_id}'. "
                "Run POST /projects/{id}/analyze first."
            )

        reqs = report.requirements or []
        status_counts: dict[str, int] = {"satisfied": 0, "partially_satisfied": 0,
                                          "not_satisfied": 0, "unclear": 0}
        for r in reqs:
            s = r.get("status", "unclear")
            status_counts[s] = status_counts.get(s, 0) + 1

        return json.dumps({
            "project_id": project_id,
            "grant_name": project.grant_name,
            "funder_name": project.funder_name,
            "deadline": project.deadline,
            "eligibility_score": report.eligibility_score,
            "readiness_score": report.readiness_score,
            "requirements_summary": {
                "total": len(reqs),
                "satisfied": status_counts["satisfied"],
                "partial": status_counts["partially_satisfied"],
                "not_met": status_counts["not_satisfied"],
                "unclear": status_counts["unclear"],
            },
            "missing_documents": report.missing_items or [],
            "risk_flags": report.risk_flags or [],
            "requirements": [
                {
                    "id": r.get("id"),
                    "text": r.get("text"),
                    "type": r.get("type"),
                    "importance": r.get("importance"),
                    "status": r.get("status"),
                    "confidence": r.get("confidence"),
                }
                for r in reqs
            ],
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool: generate_packet
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_packet(project_id: str) -> str:
    """
    Generate (or retrieve) the grant readiness PDF report for a project.

    If a PDF already exists for the current analysis, returns its path.
    Otherwise generates a fresh PDF and returns the result.
    Analysis must have been run first.

    Input:
      project_id  --  ID of the GrantPilot project

    Output JSON:
    {
      "project_id": "...",
      "report_pdf_url": "proj_xxx/report.pdf",
      "file_size_bytes": 42048,
      "download_endpoint": "/projects/{id}/report/download",
      "summary": {
        "eligibility_score": 82,
        "readiness_score": 74,
        "missing_doc_count": 2,
        "high_risk_count": 1
      }
    }
    """
    _validate_id(project_id, "project_id")
    db = _get_db()
    try:
        from app.core.config import settings
        from app.models.analysis import ReadinessReport
        from app.models.project import Project
        from app.services import report_generator, storage_service

        project = db.get(Project, project_id)
        if project is None:
            return _err(f"Project '{project_id}' not found.")

        report = (
            db.query(ReadinessReport)
            .filter(ReadinessReport.project_id == project_id)
            .first()
        )
        if report is None:
            return _err(
                f"No analysis found for project '{project_id}'. "
                "Run POST /projects/{id}/analyze first."
            )

        # Use cached PDF if it exists on disk
        storage_url = report.report_pdf_url
        if storage_url:
            pdf_path = storage_service.get_file_path(storage_url)
            if not pdf_path.exists():
                storage_url = None  # stale — regenerate

        if not storage_url:
            storage_url = report_generator.generate_and_save(db, project_id)
            db.commit()

        pdf_path = storage_service.get_file_path(storage_url)
        file_size = pdf_path.stat().st_size if pdf_path.exists() else 0

        missing_count = len([
            m for m in (report.missing_items or []) if m.get("required", False)
        ])
        high_risk_count = len([
            f for f in (report.risk_flags or []) if f.get("severity") == "high"
        ])

        return json.dumps({
            "project_id": project_id,
            "report_pdf_url": storage_url,       # relative path only — no absolute paths
            "file_size_bytes": file_size,
            "download_endpoint": f"/projects/{project_id}/report/download",
            "summary": {
                "eligibility_score": report.eligibility_score,
                "readiness_score": report.readiness_score,
                "missing_doc_count": missing_count,
                "high_risk_count": high_risk_count,
            },
        })
    except Exception as exc:
        logger.error("generate_packet failed: %s", exc)
        return _err(str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Error helper
# ---------------------------------------------------------------------------

def _err(message: str) -> str:
    return json.dumps({"error": message})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
