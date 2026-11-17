# Worker runtime

The Compose worker runs Celery from `rag_api.worker` with one process, JSON-only
serialization, durable default queue `runtime`, publisher confirms, late
acknowledgment, and prefetch one. A targeted control ping checks the actual worker
through RabbitMQ; a stopped or unreachable worker makes API readiness fail.
Probe subprocesses are killed and reaped on timeout/cancellation.

The durable job engine now provides database job/attempt state, transactional
outbox dispatch, leases, bounded retries, idempotent completion and generation
fencing. The maintenance queue runs a bounded diagnostic worker check. T007 adds isolated parsing, versioned embedding batches and generation-safe indexing.
See the [ingestion runbook](../../infra/INGESTION.md). See the [job runbook](../../infra/JOBS.md) for migration,
dispatcher activation, authenticated APIs and recovery verification.
