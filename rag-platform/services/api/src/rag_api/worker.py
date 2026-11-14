"""Bounded Celery transport; PostgreSQL leases and outbox own durable job state."""

import os

from celery import Celery

from rag_api.runtime import RuntimeSettings

settings = RuntimeSettings.from_env(os.environ)
app = Celery("rag-runtime", broker=settings.broker_url.get_secret_value())
app.conf.update(
    task_default_queue="runtime",
    task_routes={"rag.jobs.execute": {"queue": "maintenance"}},
    task_create_missing_queues=True,
    task_time_limit=90,
    task_soft_time_limit=80,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_timeout=3,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"confirm_publish": True},
    task_ignore_result=True,
)


@app.task(name="rag.jobs.execute")  # type: ignore[untyped-decorator]
def execute_job(tenant_id: str, job_id: str) -> None:
    from rag_api.identity.service import database_engine
    from rag_api.jobs.execution import execute
    from rag_api.jobs.service import JobService

    engine = database_engine(settings.database_url.get_secret_value())
    try:
        execute(JobService(engine), tenant_id, job_id)
    finally:
        engine.dispose()
