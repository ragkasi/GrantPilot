"""SQLAlchemy models for grant analysis entities.

GrantRequirement and EvidenceMatch are populated by the AI pipeline in Phase 4.
ReadinessReport is written once analysis is complete and read by the report endpoint.
All three tables exist in the schema now so the DB is ready for Phase 4 without a new migration.
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class GrantRequirement(Base):
    __tablename__ = "grant_requirements"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("projects.id"), nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False)
    source_document_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("documents.id"), nullable=True
    )
    source_page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class EvidenceMatch(Base):
    __tablename__ = "evidence_matches"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    requirement_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("grant_requirements.id"), nullable=False
    )
    document_chunk_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("document_chunks.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class ReadinessReport(Base):
    __tablename__ = "readiness_reports"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("projects.id"), nullable=False, unique=True
    )
    eligibility_score: Mapped[int] = mapped_column(Integer, nullable=False)
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    # Stored as JSON arrays — each item is a typed dict matching the API schema
    missing_items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    requirements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    draft_answers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    report_pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
