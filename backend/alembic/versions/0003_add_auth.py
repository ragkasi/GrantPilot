"""Add users table and user_id ownership column to organizations.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(200), nullable=False),
        sa.Column("is_demo", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # Nullable so existing organizations keep working; the service layer sets this
    # when creating new organizations through the API.
    op.add_column(
        "organizations",
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_organizations_user_id", "organizations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_organizations_user_id", "organizations")
    op.drop_column("organizations", "user_id")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
