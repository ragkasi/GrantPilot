"""Add embedding_json column to document_chunks.

Phase 4: stores a JSON float list per chunk for cosine-similarity retrieval.
Phase 5: replace with a native pgvector column + HNSW index.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_chunks",
        sa.Column("embedding_json", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("document_chunks", "embedding_json")
