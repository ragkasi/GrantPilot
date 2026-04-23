"""Initial schema: organizations, projects, documents, document_chunks,
grant_requirements, evidence_matches, readiness_reports.

Revision ID: 0001
Revises:
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("mission", sa.Text, nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("nonprofit_type", sa.String(50), nullable=False),
        sa.Column("annual_budget", sa.Float, nullable=False),
        sa.Column("population_served", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("organization_id", sa.String(50), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("grant_name", sa.String(300), nullable=False),
        sa.Column("grant_source_url", sa.String(500), nullable=True),
        sa.Column("funder_name", sa.String(200), nullable=True),
        sa.Column("grant_amount", sa.String(100), nullable=True),
        sa.Column("deadline", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("organization_id", sa.String(50), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("project_id", sa.String(50), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("storage_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="uploaded"),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("document_id", sa.String(50), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "grant_requirements",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("project_id", sa.String(50), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("requirement_type", sa.String(50), nullable=False),
        sa.Column("requirement_text", sa.Text, nullable=False),
        sa.Column("importance", sa.String(20), nullable=False),
        sa.Column("source_document_id", sa.String(50), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("source_page_number", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "evidence_matches",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("requirement_id", sa.String(50), sa.ForeignKey("grant_requirements.id"), nullable=False),
        sa.Column("document_chunk_id", sa.String(50), sa.ForeignKey("document_chunks.id"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("match_score", sa.Float, nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "readiness_reports",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("project_id", sa.String(50), sa.ForeignKey("projects.id"), nullable=False, unique=True),
        sa.Column("eligibility_score", sa.Integer, nullable=False),
        sa.Column("readiness_score", sa.Integer, nullable=False),
        sa.Column("missing_items", sa.JSON, nullable=False),
        sa.Column("risk_flags", sa.JSON, nullable=False),
        sa.Column("requirements", sa.JSON, nullable=False),
        sa.Column("draft_answers", sa.JSON, nullable=False),
        sa.Column("report_pdf_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Indexes for common query patterns
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_grant_requirements_project_id", "grant_requirements", ["project_id"])
    op.create_index("ix_evidence_matches_requirement_id", "evidence_matches", ["requirement_id"])


def downgrade() -> None:
    op.drop_table("readiness_reports")
    op.drop_table("evidence_matches")
    op.drop_table("grant_requirements")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("projects")
    op.drop_table("organizations")
