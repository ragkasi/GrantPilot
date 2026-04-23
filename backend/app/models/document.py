from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("organizations.id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("projects.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # Relative path within upload_dir, e.g. "proj_xxx/doc_xxx_report.pdf"
    storage_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
