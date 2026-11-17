"""Immutable revisions and generation metadata with composite tenant foreign keys."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from rag_api.identity.models import Base


class Document(Base):
    __tablename__ = "documents"
    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(36))
    source_key: Mapped[str] = mapped_column(String(512))
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "connection_id"], ["connections.tenant_id", "connections.id"]
        ),
        ForeignKeyConstraint(["tenant_id", "id"], ["work_targets.tenant_id", "work_targets.id"]),
        UniqueConstraint("tenant_id", "connection_id", "source_key"),
    )


class Revision(Base):
    __tablename__ = "document_revisions"
    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36))
    job_id: Mapped[str] = mapped_column(String(36))
    source_version: Mapped[str] = mapped_column(String(256))
    content_hash: Mapped[str] = mapped_column(String(64))
    format: Mapped[str] = mapped_column(String(16))
    generation: Mapped[int]
    processing_version: Mapped[str] = mapped_column(String(64))
    embedding_model: Mapped[str] = mapped_column(String(128))
    embedding_revision: Mapped[str] = mapped_column(String(128))
    dimensions: Mapped[int]
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    output_key: Mapped[str | None] = mapped_column(String(64))
    index_name: Mapped[str | None] = mapped_column(String(128))
    chunk_count: Mapped[int] = mapped_column(default=0)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "document_id"], ["documents.tenant_id", "documents.id"]),
        ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]),
        UniqueConstraint("tenant_id", "job_id"),
        UniqueConstraint("tenant_id", "document_id", "generation"),
    )
