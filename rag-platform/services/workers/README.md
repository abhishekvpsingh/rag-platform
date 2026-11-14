# Worker runtime

The Compose worker runs Celery from `rag_api.worker` with one process, JSON-only
serialization, durable default queue `runtime`, publisher confirms, late
acknowledgment, and prefetch one. A targeted control ping checks the actual worker
through RabbitMQ; a stopped or unreachable worker makes API readiness fail.
Probe subprocesses are killed and reaped on timeout/cancellation.

No ingestion tasks, database job state, outbox, or application retry/idempotency
implementation exists yet. Those belong to T006. The runtime control ping and
synthetic persistence exercise do not establish durable application processing.
