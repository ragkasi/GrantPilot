"""Add analysis_source and fallback_reason to readiness_reports.

These columns track whether an analysis came from the real AI pipeline,
a fallback to mock data, or the startup seed. Nullable so existing rows
are unaffected.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "readiness_reports",
        sa.Column("analysis_source", sa.String(30), nullable=True),
    )
    op.add_column(
        "readiness_reports",
        sa.Column("fallback_reason", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("readiness_reports", "fallback_reason")
    op.drop_column("readiness_reports", "analysis_source")
