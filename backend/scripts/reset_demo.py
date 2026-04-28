#!/usr/bin/env python3
"""
Reset and reseed the GrantPilot demo project to a clean demo-ready state.

Clears all analysis, documents, and chunk data for the demo project,
then re-runs the seed so the BrightPath analysis is fresh.

Usage (from the backend/ directory):
    python scripts/reset_demo.py

The demo user, organization, and project rows are preserved — only analysis
and document data is cleared.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, create_all_tables
from app.core.config import settings
from app.models.analysis import EvidenceMatch, GrantRequirement, ReadinessReport
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.project import Project
from app.services import seed as seed_service
from app.services.seed import DEMO_PROJECT_ID


def reset_demo() -> None:
    if not settings.database_url:
        # SQLite local dev — ensure tables exist
        create_all_tables()

    db = SessionLocal()
    try:
        print(f"[reset] Clearing demo data for project: {DEMO_PROJECT_ID}")

        # 1. Evidence matches for demo requirements
        req_ids = [
            r.id
            for r in db.query(GrantRequirement)
            .filter(GrantRequirement.project_id == DEMO_PROJECT_ID)
            .all()
        ]
        if req_ids:
            db.query(EvidenceMatch).filter(
                EvidenceMatch.requirement_id.in_(req_ids)
            ).delete(synchronize_session=False)
            print(f"  deleted evidence matches for {len(req_ids)} requirements")

        # 2. Grant requirements
        deleted = (
            db.query(GrantRequirement)
            .filter(GrantRequirement.project_id == DEMO_PROJECT_ID)
            .delete()
        )
        print(f"  deleted {deleted} grant requirements")

        # 3. Readiness report
        deleted = (
            db.query(ReadinessReport)
            .filter(ReadinessReport.project_id == DEMO_PROJECT_ID)
            .delete()
        )
        print(f"  deleted {deleted} readiness report(s)")

        # 4. Document chunks
        doc_ids = [
            d.id
            for d in db.query(Document)
            .filter(Document.project_id == DEMO_PROJECT_ID)
            .all()
        ]
        if doc_ids:
            deleted = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id.in_(doc_ids))
                .delete(synchronize_session=False)
            )
            print(f"  deleted {deleted} document chunks")

        # 5. Documents
        deleted = (
            db.query(Document)
            .filter(Document.project_id == DEMO_PROJECT_ID)
            .delete()
        )
        print(f"  deleted {deleted} document(s)")

        # 6. Reset project status so the seed can mark it analyzed
        project = db.get(Project, DEMO_PROJECT_ID)
        if project:
            project.status = "draft"

        db.flush()
        print("[reset] Reseeding demo data...")
        seed_service.seed_demo(db)

        # Ensure status reflects a completed demo analysis
        project = db.get(Project, DEMO_PROJECT_ID)
        if project:
            project.status = "analyzed"

        db.commit()
        print("[reset] Done.")
        print()
        print("  Demo login:  demo@grantpilot.local / DemoGrantPilot123!")
        print(f"  Project ID:  {DEMO_PROJECT_ID}")

    except Exception as exc:
        db.rollback()
        print(f"[reset] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    reset_demo()
