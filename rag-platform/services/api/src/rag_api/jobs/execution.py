"""Versioned, installed handlers only. No source/model-supplied code is executed."""

import time

from rag_api.jobs.service import JobService


def execute(service: JobService, tenant_id: str, job_id: str) -> None:
    lease = service.claim(tenant_id, job_id)
    if lease is None:
        return
    if lease.kind != "worker_check" or lease.processing_version != "worker-check-v1":
        service.fail(lease, transient=False)
        return
    try:
        # Real worker scheduling/heartbeat exercise, explicitly separate from ingestion.
        for elapsed in range(lease.duration_seconds):
            time.sleep(1)
            if not service.heartbeat(
                lease, int(99 * (elapsed + 1) / max(1, lease.duration_seconds))
            ):
                return
        service.complete(lease)
    except Exception:
        # Never store task exception text; future handlers classify retryable errors explicitly.
        service.fail(lease, transient=True)
