"""Bounded Celery runtime; durable application jobs arrive in T006."""

import os

from celery import Celery

from rag_api.runtime import RuntimeSettings

settings = RuntimeSettings.from_env(os.environ)
app = Celery("rag-runtime", broker=settings.broker_url.get_secret_value())
app.conf.update(
    task_default_queue="runtime",
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
