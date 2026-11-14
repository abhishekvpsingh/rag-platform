"""Tenant-safe jobs, fenced attempts, outbox and generation publication records."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from rag_api.identity.models import Base


class WorkTarget(Base):
    __tablename__ = "work_targets"
    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36))
    generation: Mapped[int] = mapped_column(default=1)
    tombstoned: Mapped[bool] = mapped_column(default=False)
    active_generation: Mapped[int | None]
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "owner_id"], ["memberships.tenant_id", "memberships.user_id"]
        ),
        CheckConstraint("generation > 0"),
    )


class Job(Base):
    __tablename__ = "jobs"
    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36))
    target_id: Mapped[str] = mapped_column(String(36))
    generation: Mapped[int]
    kind: Mapped[str] = mapped_column(String(32))
    processing_version: Mapped[str] = mapped_column(String(32))
    idempotency_key: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), default="queued")
    attempts: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=3)
    progress: Mapped[int] = mapped_column(default=0)
    # Bounded diagnostic work duration, no source content or arbitrary executable payload.
    duration_seconds: Mapped[int] = mapped_column(default=0)
    lease_token: Mapped[str | None] = mapped_column(String(36))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(32))
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "owner_id"], ["memberships.tenant_id", "memberships.user_id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_id"], ["work_targets.tenant_id", "work_targets.id"]
        ),
        UniqueConstraint("tenant_id", "owner_id", "idempotency_key"),
        CheckConstraint(
            "state IN ('queued','running','retrying','succeeded','failed','cancelled','superseded')"
        ),
        CheckConstraint("attempts >= 0 AND max_attempts BETWEEN 1 AND 5"),
        CheckConstraint("progress BETWEEN 0 AND 100 AND duration_seconds BETWEEN 0 AND 60"),
    )


class JobAttempt(Base):
    __tablename__ = "job_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36))
    job_id: Mapped[str] = mapped_column(String(36))
    number: Mapped[int]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str] = mapped_column(String(32))
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]),
        UniqueConstraint("tenant_id", "job_id", "number"),
    )


class OutboxEvent(Base):
    __tablename__ = "job_outbox"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36))
    job_id: Mapped[str] = mapped_column(String(36))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    lock_token: Mapped[str | None] = mapped_column(String(36))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failures: Mapped[int] = mapped_column(default=0)
    abandoned: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]),)


class JobResult(Base):
    __tablename__ = "job_results"
    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    target_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    generation: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36))
    output_ref: Mapped[str] = mapped_column(String(255))
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "target_id"], ["work_targets.tenant_id", "work_targets.id"]
        ),
        ForeignKeyConstraint(["tenant_id", "job_id"], ["jobs.tenant_id", "jobs.id"]),
    )
