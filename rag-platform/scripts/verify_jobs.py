"""Real RabbitMQ/Celery worker-kill and publish-recovery acceptance on a disposable DB."""

import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from celery import Celery
from rag_api.identity.crypto import CredentialCipher
from rag_api.identity.service import IdentityService, database_engine
from rag_api.jobs.dispatcher import dispatch_batch
from rag_api.jobs.models import Job, JobAttempt, JobResult
from rag_api.jobs.service import JobService
from sqlalchemy import func, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]


def wait_until(check: Callable[[], bool], timeout: int = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(1)
    raise AssertionError("Job integration condition timed out")


def main() -> None:
    # Caller supplies only a newly created, disposable test database.
    database_url = os.environ["RAG_DATABASE_URL"]
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    engine = database_engine(database_url)
    service = JobService(engine)
    identity = IdentityService(engine, CredentialCipher({"test": secrets.token_bytes(32)}, "test"))
    password = secrets.token_urlsafe(24)
    identity.bootstrap("jobs@example.test", password)
    token = identity.login("jobs@example.test", password).token
    name = "rag-jobs-test-" + uuid4().hex[:12]
    broker_password = secrets.token_urlsafe(32)
    env = {
        **os.environ,
        "RABBITMQ_DEFAULT_USER": "fixture",
        "RABBITMQ_DEFAULT_PASS": broker_password,
    }
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        broker_port = reservation.getsockname()[1]
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-e",
            "RABBITMQ_DEFAULT_USER",
            "-e",
            "RABBITMQ_DEFAULT_PASS",
            "-p",
            f"127.0.0.1:{broker_port}:5672",
            "rabbitmq:4.1.4-management",
        ],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    worker: subprocess.Popen[bytes] | None = None
    try:
        port = (
            subprocess.check_output(["docker", "port", name, "5672"], text=True)
            .strip()
            .rsplit(":", 1)[1]
        )
        broker_url = f"amqp://fixture:{broker_password}@127.0.0.1:{port}//"
        app = Celery("acceptance", broker=broker_url)
        app.conf.update(
            broker_connection_timeout=2,
            broker_transport_options={"confirm_publish": True},
            task_serializer="json",
            accept_content=["json"],
        )

        def broker_ready() -> bool:
            try:
                with app.connection_for_write(connect_timeout=2) as connection:
                    connection.ensure_connection(max_retries=0)
                return True
            except Exception:
                return False

        wait_until(broker_ready)
        print("Disposable broker is ready", flush=True)

        def publish(tenant_id: str, job_id: str) -> None:
            app.send_task(
                "rag.jobs.execute",
                args=[tenant_id, job_id],
                queue="maintenance",
                task_id=job_id,
                retry=False,
                delivery_mode=2,
                timeout=3,
                confirm_timeout=3,
            )

        def state(job_id: str) -> str:
            with Session(engine) as db:
                job = db.get(Job, (identity.authenticate(token).tenant_id, job_id))
                assert job is not None
                return job.state

        runtime_env = {
            **env,
            "RAG_DATABASE_URL": database_url,
            "RAG_BROKER_URL": broker_url,
            "RAG_SEARCH_URL": "https://127.0.0.1:9200",
            "RAG_SEARCH_USERNAME": "fixture",
            "RAG_SEARCH_PASSWORD": secrets.token_urlsafe(24),
            "RAG_ARTIFACT_ROOT": tempfile.gettempdir(),
            "PYTHONPATH": str(ROOT / "services/api/src"),
        }

        def start_worker() -> subprocess.Popen[bytes]:
            return subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "rag_api.worker:app",
                    "worker",
                    "--pool=solo",
                    "--concurrency=1",
                    "--queues=maintenance",
                    "--hostname=acceptance@worker",
                    "--loglevel=CRITICAL",
                    "--without-gossip",
                    "--without-mingle",
                ],
                cwd=ROOT,
                env=runtime_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        # A committed job survives a real broker outage before publication.
        replayed = service.submit_check(token, "broker-outage")
        subprocess.run(
            ["docker", "stop", "--time", "5", name], check=True, stdout=subprocess.DEVNULL
        )
        assert dispatch_batch(service, publish) == 0
        assert state(replayed.id) == "queued"
        subprocess.run(["docker", "start", name], check=True, stdout=subprocess.DEVNULL)
        wait_until(broker_ready)
        print("Disposable broker is ready", flush=True)
        worker = start_worker()
        assert dispatch_batch(service, publish) == 1
        wait_until(lambda: state(replayed.id) == "succeeded")
        print("Broker outage publication replay passed", flush=True)
        publish(replayed.tenant_id, replayed.id)
        publish(replayed.tenant_id, replayed.id)

        # Kill a real consuming worker after it owns a lease, then recover from PostgreSQL.
        interrupted = service.submit_check(token, "worker-kill", 8)
        dispatch_batch(service, publish)
        wait_until(lambda: state(interrupted.id) == "running")
        os.killpg(worker.pid, signal.SIGKILL)
        worker.wait(timeout=10)
        worker = start_worker()

        def recovered() -> bool:
            service.recover()
            dispatch_batch(service, publish)
            return state(interrupted.id) == "succeeded"

        wait_until(recovered)
        print("Killed worker recovered", flush=True)
        with Session(engine) as db:
            for job in (replayed, interrupted):
                assert (
                    db.scalar(
                        select(func.count())
                        .select_from(JobResult)
                        .where(JobResult.job_id == job.id)
                    )
                    == 1
                )
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(JobAttempt)
                    .where(JobAttempt.job_id == interrupted.id)
                )
                == 2
            )

        # A real in-flight worker cannot publish after a tombstone or cancellation.
        deleted = service.submit_check(token, "delete-running", 8)
        dispatch_batch(service, publish)
        wait_until(lambda: state(deleted.id) == "running")
        service.invalidate_target(token, deleted.id, True)
        wait_until(lambda: state(deleted.id) == "superseded")
        cancelled = service.submit_check(token, "cancel-running", 8)
        dispatch_batch(service, publish)
        wait_until(lambda: state(cancelled.id) == "running")
        service.cancel(token, cancelled.id)
        time.sleep(2)
        assert state(cancelled.id) == "cancelled"
        with Session(engine) as db:
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(JobResult)
                    .where(JobResult.job_id.in_([deleted.id, cancelled.id]))
                )
                == 0
            )
        app.close()
        print(
            "Real RabbitMQ publish replay, duplicate delivery, worker kill, "
            "deletion and cancellation passed"
        )
    finally:
        if worker is not None and worker.poll() is None:
            os.killpg(worker.pid, signal.SIGTERM)
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(worker.pid, signal.SIGKILL)
                worker.wait(timeout=5)
        engine.dispose()
        subprocess.run(["docker", "rm", "-f", "-v", name], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
