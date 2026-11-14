"""Durable state machine. Database transactions fence duplicate and obsolete workers."""

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import Engine, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rag_api.identity.models import Membership, User
from rag_api.identity.service import AccessDenied, IdentityService, Principal, digest, now, utc
from rag_api.jobs.models import Job, JobAttempt, JobResult, OutboxEvent, WorkTarget

TERMINAL = {"succeeded", "failed", "cancelled", "superseded"}


class JobConflict(Exception):
    """Safe conflict with no resource details."""


@dataclass(frozen=True)
class Lease:
    tenant_id: str
    job_id: str
    token: str
    kind: str
    duration_seconds: int
    processing_version: str


@dataclass(frozen=True)
class Delivery:
    event_id: str
    tenant_id: str
    job_id: str
    token: str


class JobService:
    def __init__(
        self, engine: Engine, clock: Callable[[], datetime] = now, lease_seconds: int = 30
    ) -> None:
        self.engine = engine
        self.clock = clock
        self.lease_seconds = lease_seconds

    @staticmethod
    def event(db: Session, job: Job, available_at: datetime) -> None:
        db.add(
            OutboxEvent(
                id=str(uuid4()),
                tenant_id=job.tenant_id,
                job_id=job.id,
                available_at=available_at,
                failures=0,
            )
        )

    @staticmethod
    def lock_job(db: Session, tenant_id: str, job_id: str) -> Job | None:
        return db.scalar(
            select(Job).where(Job.tenant_id == tenant_id, Job.id == job_id).with_for_update()
        )

    @staticmethod
    def target(db: Session, job: Job) -> WorkTarget:
        target = db.scalar(
            select(WorkTarget)
            .where(WorkTarget.tenant_id == job.tenant_id, WorkTarget.id == job.target_id)
            .with_for_update()
        )
        assert target is not None
        return target

    @staticmethod
    def valid_owner(db: Session, job: Job) -> bool:
        membership = db.get(Membership, (job.tenant_id, job.owner_id))
        user = db.get(User, job.owner_id)
        return bool(membership and membership.active and user and user.active)

    def finish_attempt(self, db: Session, job: Job, outcome: str) -> None:
        if job.lease_token:
            attempt = db.get(JobAttempt, job.lease_token)
            if attempt is not None:
                attempt.outcome = outcome
                attempt.ended_at = self.clock()
        job.lease_token = None
        job.lease_until = None
        job.updated_at = self.clock()

    def invalidate_if_needed(self, db: Session, job: Job) -> bool:
        target = self.target(db, job)
        if (
            target.tombstoned
            or target.generation != job.generation
            or target.owner_id != job.owner_id
            or not self.valid_owner(db, job)
        ):
            job.state = "superseded"
            job.error_code = "work_invalidated"
            self.finish_attempt(db, job, "superseded")
            return True
        return False

    def submit_check(self, token: str, idempotency_key: str, duration_seconds: int = 0) -> Job:
        """Real bounded diagnostic task; this is not source ingestion."""
        if not 1 <= len(idempotency_key) <= 128 or not 0 <= duration_seconds <= 60:
            raise ValueError("Invalid job request")
        key = digest(idempotency_key)
        try:
            with Session(self.engine, expire_on_commit=False) as db, db.begin():
                principal = IdentityService.resolve(db, token)
                if principal.role not in {"owner", "admin"}:
                    raise AccessDenied()
                db.scalar(
                    select(Membership)
                    .where(
                        Membership.tenant_id == principal.tenant_id,
                        Membership.user_id == principal.user_id,
                    )
                    .with_for_update()
                )
                existing = db.scalar(
                    select(Job).where(
                        Job.tenant_id == principal.tenant_id,
                        Job.owner_id == principal.user_id,
                        Job.idempotency_key == key,
                    )
                )
                if existing:
                    if existing.duration_seconds != duration_seconds:
                        raise JobConflict()
                    return existing
                active_count = db.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(
                        Job.tenant_id == principal.tenant_id,
                        Job.owner_id == principal.user_id,
                        Job.state.not_in(TERMINAL),
                    )
                )
                if active_count is not None and active_count >= 100:
                    raise JobConflict()
                target_id = str(
                    uuid5(NAMESPACE_URL, f"{principal.tenant_id}/{principal.user_id}/{key}")
                )
                target = WorkTarget(
                    tenant_id=principal.tenant_id,
                    id=target_id,
                    owner_id=principal.user_id,
                    generation=1,
                    tombstoned=False,
                )
                db.add(target)
                db.flush()
                job = Job(
                    tenant_id=principal.tenant_id,
                    id=str(uuid4()),
                    owner_id=principal.user_id,
                    target_id=target_id,
                    generation=1,
                    kind="worker_check",
                    processing_version="worker-check-v1",
                    idempotency_key=key,
                    state="queued",
                    attempts=0,
                    max_attempts=3,
                    progress=0,
                    duration_seconds=duration_seconds,
                    available_at=self.clock(),
                    created_at=self.clock(),
                    updated_at=self.clock(),
                )
                db.add(job)
                db.flush()
                self.event(db, job, self.clock())
                IdentityService.audit(db, principal, "job.created")
                return job
        except IntegrityError:
            # Concurrent idempotent submissions converge without partial targets/outbox rows.
            with Session(self.engine) as db:
                principal = IdentityService.resolve(db, token)
                existing = db.scalar(
                    select(Job).where(
                        Job.tenant_id == principal.tenant_id,
                        Job.owner_id == principal.user_id,
                        Job.idempotency_key == key,
                    )
                )
                if existing is None or existing.duration_seconds != duration_seconds:
                    raise JobConflict() from None
                return existing

    def list_jobs(self, token: str, before: datetime | None = None) -> list[Job]:
        with Session(self.engine) as db:
            principal = IdentityService.resolve(db, token)
            query = select(Job).where(
                Job.tenant_id == principal.tenant_id, Job.owner_id == principal.user_id
            )
            if before:
                query = query.where(Job.created_at < before)
            return list(db.scalars(query.order_by(Job.created_at.desc(), Job.id.desc()).limit(50)))

    def owned(self, db: Session, token: str, job_id: str) -> tuple[Principal, Job]:
        principal = IdentityService.resolve(db, token)
        job = self.lock_job(db, principal.tenant_id, job_id)
        if job is None or job.owner_id != principal.user_id:
            raise AccessDenied()
        return principal, job

    def cancel(self, token: str, job_id: str) -> None:
        with Session(self.engine) as db, db.begin():
            principal, job = self.owned(db, token, job_id)
            if job.state not in TERMINAL:
                job.state = "cancelled"
                self.finish_attempt(db, job, "cancelled")
                IdentityService.audit(db, principal, "job.cancelled")

    def replay(self, token: str, job_id: str) -> None:
        with Session(self.engine) as db, db.begin():
            principal, job = self.owned(db, token, job_id)
            if principal.role not in {"owner", "admin"} or job.state != "failed":
                raise JobConflict()
            target = self.target(db, job)
            if target.tombstoned or target.generation != job.generation:
                raise JobConflict()
            # Explicit operator replay grants a new bounded attempt budget, preserving history.
            job.max_attempts = min(5, job.attempts + 2)
            if job.attempts >= job.max_attempts:
                raise JobConflict()
            job.state, job.error_code = "queued", None
            job.available_at = job.updated_at = self.clock()
            self.event(db, job, self.clock())
            IdentityService.audit(db, principal, "job.replayed")

    def invalidate_target(self, token: str, job_id: str, tombstone: bool) -> None:
        """Internal lifecycle boundary for future source revisions/deletions."""
        with Session(self.engine) as db, db.begin():
            principal, job = self.owned(db, token, job_id)
            target = self.target(db, job)
            target.generation += 1
            target.tombstoned = target.tombstoned or tombstone
            target.active_generation = None
            IdentityService.audit(db, principal, "work.invalidated")

    def claim(self, tenant_id: str, job_id: str) -> Lease | None:
        with Session(self.engine) as db, db.begin():
            job = self.lock_job(db, tenant_id, job_id)
            if job is None or job.state in TERMINAL:
                return None
            current = self.clock()
            if job.state == "running" and job.lease_until and utc(job.lease_until) > current:
                return None
            if utc(job.available_at) > current or self.invalidate_if_needed(db, job):
                return None
            if job.state == "running":
                self.finish_attempt(db, job, "lease_expired")
            if job.attempts >= job.max_attempts:
                job.state, job.error_code = "failed", "attempts_exhausted"
                return None
            job.attempts += 1
            job.state = "running"
            job.lease_token = str(uuid4())
            job.lease_until = current + timedelta(seconds=self.lease_seconds)
            job.updated_at = current
            job.error_code = None
            db.add(
                JobAttempt(
                    id=job.lease_token,
                    tenant_id=tenant_id,
                    job_id=job_id,
                    number=job.attempts,
                    started_at=current,
                    outcome="running",
                )
            )
            return Lease(
                tenant_id,
                job_id,
                job.lease_token,
                job.kind,
                job.duration_seconds,
                job.processing_version,
            )

    def live_lease(self, db: Session, lease: Lease) -> Job | None:
        job = self.lock_job(db, lease.tenant_id, lease.job_id)
        if (
            job is None
            or job.state != "running"
            or job.lease_token != lease.token
            or job.lease_until is None
            or utc(job.lease_until) <= self.clock()
        ):
            return None
        return job

    def heartbeat(self, lease: Lease, progress: int) -> bool:
        with Session(self.engine) as db, db.begin():
            job = self.live_lease(db, lease)
            if job is None or self.invalidate_if_needed(db, job):
                return False
            job.progress = max(job.progress, min(99, max(0, progress)))
            job.updated_at = self.clock()
            job.lease_until = self.clock() + timedelta(seconds=self.lease_seconds)
            return True

    def complete(self, lease: Lease) -> bool:
        with Session(self.engine) as db, db.begin():
            job = self.live_lease(db, lease)
            if job is None or self.invalidate_if_needed(db, job):
                return False
            target = self.target(db, job)
            # The visibility pointer and immutable output record commit with success.
            db.add(
                JobResult(
                    tenant_id=job.tenant_id,
                    target_id=job.target_id,
                    generation=job.generation,
                    job_id=job.id,
                    output_ref="worker-check:ok",
                )
            )
            target.active_generation = job.generation
            job.state, job.progress = "succeeded", 100
            self.finish_attempt(db, job, "succeeded")
            return True

    def fail(self, lease: Lease, transient: bool) -> None:
        with Session(self.engine) as db, db.begin():
            job = self.live_lease(db, lease)
            if job is None or self.invalidate_if_needed(db, job):
                return
            self.finish_attempt(db, job, "transient_error" if transient else "permanent_error")
            job.error_code = "transient_error" if transient else "permanent_error"
            if transient and job.attempts < job.max_attempts:
                job.state = "retrying"
                delay = min(60, 2**job.attempts) + random.uniform(0, 1)
                job.available_at = self.clock() + timedelta(seconds=delay)
                self.event(db, job, job.available_at)
            else:
                job.state = "failed"

    def recover(self) -> int:
        """Bounded database sweep; lost deliveries and dead workers cannot strand jobs."""
        current = self.clock()
        count = 0
        pending_delivery = (
            select(OutboxEvent.id)
            .where(
                OutboxEvent.tenant_id == Job.tenant_id,
                OutboxEvent.job_id == Job.id,
                OutboxEvent.published_at.is_(None),
                OutboxEvent.abandoned.is_(False),
            )
            .exists()
        )
        with Session(self.engine) as db, db.begin():
            jobs = list(
                db.scalars(
                    select(Job)
                    .where(
                        or_(
                            (Job.state == "running") & (Job.lease_until <= current),
                            Job.state.in_(["queued", "retrying"])
                            & (Job.updated_at <= current - timedelta(seconds=60))
                            & (Job.available_at <= current)
                            & ~pending_delivery,
                        )
                    )
                    .order_by(Job.updated_at)
                    .limit(100)
                    .with_for_update(skip_locked=True)
                )
            )
            for job in jobs:
                if self.invalidate_if_needed(db, job):
                    continue
                if job.state == "running":
                    self.finish_attempt(db, job, "lease_expired")
                if job.attempts >= job.max_attempts:
                    job.state, job.error_code = "failed", "attempts_exhausted"
                    continue
                job.state = "queued"
                job.updated_at = job.available_at = current
                self.event(db, job, current)
                count += 1
        return count

    def next_delivery(self) -> Delivery | None:
        with Session(self.engine) as db, db.begin():
            event = db.scalar(
                select(OutboxEvent)
                .where(
                    OutboxEvent.published_at.is_(None),
                    OutboxEvent.abandoned.is_(False),
                    OutboxEvent.available_at <= self.clock(),
                    or_(
                        OutboxEvent.locked_until.is_(None), OutboxEvent.locked_until <= self.clock()
                    ),
                )
                .order_by(OutboxEvent.available_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if event is None:
                return None
            event.lock_token = str(uuid4())
            event.locked_until = self.clock() + timedelta(seconds=30)
            return Delivery(event.id, event.tenant_id, event.job_id, event.lock_token)

    def delivery_result(self, delivery: Delivery, succeeded: bool) -> None:
        with Session(self.engine) as db, db.begin():
            job = self.lock_job(db, delivery.tenant_id, delivery.job_id)
            event = db.scalar(
                select(OutboxEvent)
                .where(
                    OutboxEvent.id == delivery.event_id, OutboxEvent.lock_token == delivery.token
                )
                .with_for_update()
            )
            if event is None:
                return
            if succeeded:
                event.published_at = self.clock()
            else:
                event.failures += 1
                if event.failures >= 10:
                    event.abandoned = True
                    if job is not None and job.state in {"queued", "retrying"}:
                        job.state, job.error_code = "failed", "dispatch_exhausted"
                        job.updated_at = self.clock()
                event.available_at = self.clock() + timedelta(
                    seconds=min(60, 2 ** min(event.failures, 6))
                )
            event.lock_token, event.locked_until = None, None
