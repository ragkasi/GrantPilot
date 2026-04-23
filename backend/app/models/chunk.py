"""DocumentChunk — one searchable piece of a parsed document.

Each chunk carries enough metadata to produce a citation without additional
queries: document_name and page_number are denormalized here intentionally.
Phase 4 will add an `embedding` column (pgvector) for RAG retrieval.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("documents.id"), nullable=False
    )
    # Denormalized so RAG results carry full citation info without joins
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    # embedding column added in Phase 4 (pgvector / JSON float list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
