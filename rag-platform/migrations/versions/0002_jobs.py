"""Durable jobs, attempt fencing, transactional outbox and generation guards."""

import sqlalchemy as sa
from alembic import op

revision = "0002_jobs"
down_revision = "0001_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_targets",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("tombstoned", sa.Boolean(), nullable=False),
        sa.Column("active_generation", sa.Integer(), nullable=True),
        sa.CheckConstraint("generation > 0"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_id"],
            ["memberships.tenant_id", "memberships.user_id"],
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
    )
    op.create_table(
        "jobs",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("processing_version", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.String(length=36), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.CheckConstraint(
            "state IN ('queued','running','retrying','succeeded','failed','cancelled','superseded')"
        ),
        sa.CheckConstraint("attempts >= 0 AND max_attempts BETWEEN 1 AND 5"),
        sa.CheckConstraint("progress BETWEEN 0 AND 100 AND duration_seconds BETWEEN 0 AND 60"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_id"],
            ["memberships.tenant_id", "memberships.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "target_id"],
            ["work_targets.tenant_id", "work_targets.id"],
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "owner_id", "idempotency_key"),
    )
    op.create_table(
        "job_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "job_id"],
            ["jobs.tenant_id", "jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "job_id", "number"),
    )
    op.create_table(
        "job_outbox",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lock_token", sa.String(length=36), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("abandoned", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "job_id"],
            ["jobs.tenant_id", "jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_job_outbox_available_at"), "job_outbox", ["available_at"], unique=False
    )
    op.create_table(
        "job_results",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("output_ref", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "job_id"],
            ["jobs.tenant_id", "jobs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "target_id"],
            ["work_targets.tenant_id", "work_targets.id"],
        ),
        sa.PrimaryKeyConstraint("tenant_id", "target_id", "generation"),
    )


def downgrade() -> None:
    op.drop_table("job_results")
    op.drop_index(op.f("ix_job_outbox_available_at"), table_name="job_outbox")
    op.drop_table("job_outbox")
    op.drop_table("job_attempts")
    op.drop_table("jobs")
    op.drop_table("work_targets")
