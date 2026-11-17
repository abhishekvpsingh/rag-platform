"""Immutable source revisions and indexing generations."""

import sqlalchemy as sa
from alembic import op

revision = "0003_ingestion"
down_revision = "0002_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("source_key", sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connection_id"],
            ["connections.tenant_id", "connections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "id"],
            ["work_targets.tenant_id", "work_targets.id"],
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "connection_id", "source_key"),
    )
    op.create_table(
        "document_revisions",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("source_version", sa.String(length=256), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("processing_version", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("embedding_revision", sa.String(length=128), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("output_key", sa.String(length=64), nullable=True),
        sa.Column("index_name", sa.String(length=128), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["documents.tenant_id", "documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "job_id"],
            ["jobs.tenant_id", "jobs.id"],
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "document_id", "generation"),
        sa.UniqueConstraint("tenant_id", "job_id"),
    )


def downgrade() -> None:
    op.drop_table("document_revisions")
    op.drop_table("documents")
