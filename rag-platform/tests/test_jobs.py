"""Durability, ownership and publication invariants, also run on PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from rag_api.identity.http import COOKIE
from rag_api.identity.service import AccessDenied, IdentityService, now
from rag_api.jobs.dispatcher import dispatch_batch
from rag_api.jobs.http import jobs_router
from rag_api.jobs.models import Job, JobAttempt, JobResult, OutboxEvent, WorkTarget
from rag_api.jobs.service import JobConflict, JobService
from rag_api.main import create_app
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_identity import member, owner


@pytest.fixture(name="identity")
def job_identity(service: IdentityService) -> IdentityService:
    return service


class Clock:
    def __init__(self) -> None:
        self.value = now()

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def test_duplicate_delivery_and_idempotent_creation(identity: IdentityService) -> None:
    token = owner(identity)
    service = JobService(identity.engine)
    job = service.submit_check(token, "one")
    assert service.submit_check(token, "one").id == job.id
    with pytest.raises(JobConflict):
        service.submit_check(token, "one", 1)
    lease = service.claim(job.tenant_id, job.id)
    assert lease and service.claim(job.tenant_id, job.id) is None
    assert service.complete(lease) and not service.complete(lease)
    assert service.claim(job.tenant_id, job.id) is None
    with Session(identity.engine) as db:
        for model in (Job, JobAttempt, JobResult, OutboxEvent):
            assert db.scalar(select(func.count()).select_from(model)) == 1
        target = db.get(WorkTarget, (job.tenant_id, job.target_id))
        assert target and target.active_generation == 1


def test_concurrent_submit_and_claim(identity: IdentityService) -> None:
    if identity.engine.dialect.name != "postgresql":
        pytest.skip("Row-lock concurrency is verified against PostgreSQL")
    token = owner(identity)
    service = JobService(identity.engine)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = list(pool.map(lambda _: service.submit_check(token, "concurrent"), range(2)))
    assert jobs[0].id == jobs[1].id
    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(lambda _: service.claim(jobs[0].tenant_id, jobs[0].id), range(2)))
    assert sum(lease is not None for lease in leases) == 1


def test_dead_worker_lease_fencing_and_heartbeat(identity: IdentityService) -> None:
    token, clock = owner(identity), Clock()
    service = JobService(identity.engine, clock, lease_seconds=5)
    job = service.submit_check(token, "lease")
    old = service.claim(job.tenant_id, job.id)
    assert old
    clock.advance(4)
    assert service.heartbeat(old, 20)
    clock.advance(2)
    assert service.recover() == 0
    clock.advance(4)
    assert service.recover() == 1
    new = service.claim(job.tenant_id, job.id)
    assert new and new.token != old.token
    assert not service.complete(old) and not service.heartbeat(old, 100)
    assert service.complete(new)
    with Session(identity.engine) as db:
        assert list(db.scalars(select(JobAttempt.outcome).order_by(JobAttempt.number))) == [
            "lease_expired",
            "succeeded",
        ]
        assert db.scalar(select(func.count()).select_from(JobResult)) == 1


@pytest.mark.parametrize("tombstone", [True, False])
def test_stale_generation_never_publishes(identity: IdentityService, tombstone: bool) -> None:
    token = owner(identity)
    service = JobService(identity.engine)
    job = service.submit_check(token, "generation")
    lease = service.claim(job.tenant_id, job.id)
    assert lease
    service.invalidate_target(token, job.id, tombstone)
    assert not service.complete(lease)
    assert service.claim(job.tenant_id, job.id) is None
    with Session(identity.engine) as db:
        target = db.get(WorkTarget, (job.tenant_id, job.target_id))
        assert target and target.active_generation is None
        assert db.scalar(select(func.count()).select_from(JobResult)) == 0
    assert service.list_jobs(token)[0].state == "superseded"


def test_cancel_and_owner_isolation(identity: IdentityService) -> None:
    token = owner(identity)
    same = member(identity, identity.authenticate(token).tenant_id)
    other = member(identity)
    service = JobService(identity.engine)
    job = service.submit_check(token, "private")
    for forbidden in (same, other):
        assert service.list_jobs(forbidden) == []
        with pytest.raises(AccessDenied):
            service.cancel(forbidden, job.id)
        with pytest.raises(AccessDenied):
            service.invalidate_target(forbidden, job.id, True)
    lease = service.claim(job.tenant_id, job.id)
    assert lease
    service.cancel(token, job.id)
    assert not service.heartbeat(lease, 50) and not service.complete(lease)
    assert service.list_jobs(token)[0].state == "cancelled"


def test_bounded_retries_and_explicit_replay(identity: IdentityService) -> None:
    token, clock = owner(identity), Clock()
    service = JobService(identity.engine, clock)
    job = service.submit_check(token, "retries")
    for _ in range(3):
        lease = service.claim(job.tenant_id, job.id)
        assert lease
        service.fail(lease, True)
        assert service.claim(job.tenant_id, job.id) is None
        clock.advance(65)
    assert service.list_jobs(token)[0].state == "failed"
    service.replay(token, job.id)
    lease = service.claim(job.tenant_id, job.id)
    assert lease and service.complete(lease)
    with pytest.raises(JobConflict):
        service.replay(token, job.id)


def test_outbox_failure_and_publish_before_crash(identity: IdentityService) -> None:
    token, clock = owner(identity), Clock()
    service = JobService(identity.engine, clock)
    job = service.submit_check(token, "outbox")

    def unavailable(tenant: str, job_id: str) -> None:
        raise OSError("synthetic outage")

    assert dispatch_batch(service, unavailable) == 0
    clock.advance(5)
    first = service.next_delivery()
    assert first and first.job_id == job.id
    clock.advance(31)
    second = service.next_delivery()
    assert second and second.event_id == first.event_id and second.token != first.token
    service.delivery_result(first, True)
    with Session(identity.engine) as db:
        event = db.get(OutboxEvent, first.event_id)
        assert event and event.published_at is None
    service.delivery_result(second, True)
    assert service.next_delivery() is None
    lease = service.claim(job.tenant_id, job.id)
    assert lease and service.complete(lease)
    assert service.claim(job.tenant_id, job.id) is None


def test_job_http_authorization_csrf_and_status(identity: IdentityService) -> None:
    token = owner(identity)
    service = JobService(identity.engine)
    job = service.submit_check(token, "http")
    app = create_app()
    app.include_router(jobs_router(identity, "https://app.example.test"))
    with TestClient(app, base_url="https://app.example.test") as client:
        assert client.get("/api/v1/jobs").status_code == 401
        client.cookies.set(COOKIE, token)
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert response.json()[0]["id"] == job.id
        assert "tenant_id" not in response.json()[0] and "lease_token" not in response.json()[0]
        assert client.post(f"/api/v1/jobs/{job.id}/cancel").status_code == 403
        client.cookies.set(COOKIE, member(identity))
        assert client.get("/api/v1/jobs").json() == []


def test_dispatch_retry_budget_and_replay(identity: IdentityService) -> None:
    token, clock = owner(identity), Clock()
    service = JobService(identity.engine, clock)
    job = service.submit_check(token, "dispatch-budget")
    for _ in range(10):
        delivery = service.next_delivery()
        assert delivery
        service.delivery_result(delivery, False)
        clock.advance(65)
        # Pending outbox messages are not multiplied by the recovery sweep.
        service.recover()
    assert service.list_jobs(token)[0].state == "failed"
    assert service.list_jobs(token)[0].error_code == "dispatch_exhausted"
    assert service.next_delivery() is None
    service.replay(token, job.id)
    assert service.next_delivery() is not None


def test_revoked_membership_fences_running_work(identity: IdentityService) -> None:
    from rag_api.identity.models import Membership

    token = owner(identity)
    principal = identity.authenticate(token)
    service = JobService(identity.engine)
    job = service.submit_check(token, "revoke")
    lease = service.claim(job.tenant_id, job.id)
    assert lease
    with Session(identity.engine) as db, db.begin():
        membership = db.get(Membership, (principal.tenant_id, principal.user_id))
        assert membership
        membership.active = False
    assert not service.complete(lease)
    with Session(identity.engine) as db:
        assert db.scalar(select(func.count()).select_from(JobResult)) == 0
