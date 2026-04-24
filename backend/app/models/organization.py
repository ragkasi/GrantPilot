from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    # Nullable so existing rows survive migration; set by service layer on create.
    user_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("users.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    mission: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    nonprofit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    annual_budget: Mapped[float] = mapped_column(Float, nullable=False)
    population_served: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
