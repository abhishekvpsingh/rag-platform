"""Replay the transactional outbox with broker confirms; sweep abandoned leases."""

import logging
import os
import signal
import threading
from collections.abc import Callable

from rag_api.identity.service import database_engine
from rag_api.jobs.service import JobService

logger = logging.getLogger(__name__)


def dispatch_batch(
    service: JobService, publish: Callable[[str, str], None], limit: int = 100
) -> int:
    delivered = 0
    for _ in range(limit):
        delivery = service.next_delivery()
        if delivery is None:
            break
        try:
            publish(delivery.tenant_id, delivery.job_id)
        except Exception:
            service.delivery_result(delivery, False)
        else:
            service.delivery_result(delivery, True)
            delivered += 1
    return delivered


def main() -> None:
    from rag_api.worker import app

    engine = database_engine(os.environ["RAG_DATABASE_URL"])
    service = JobService(engine)
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())

    def publish(tenant_id: str, job_id: str) -> None:
        app.send_task(
            "rag.jobs.execute",
            args=[tenant_id, job_id],
            queue="maintenance",
            task_id=job_id,
            retry=False,
            delivery_mode=2,
            timeout=5,
            confirm_timeout=5,
        )

    try:
        while not stopped.is_set():
            try:
                service.recover()
                dispatch_batch(service, publish)
            except Exception:
                logger.warning("Job dispatcher unavailable; recovery will resume")
            stopped.wait(2)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
