from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow

# Mirrors ProjectStatus in schemas/project.py — kept as a plain string column
# so SQLite and Postgres both work without an Enum type.


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("organizations.id"), nullable=False
    )
    grant_name: Mapped[str] = mapped_column(String(300), nullable=False)
    grant_source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    funder_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    grant_amount: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deadline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
