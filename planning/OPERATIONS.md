# Operations

## Observability

Expose structured logs, metrics, and distributed traces with correlation IDs. Track connector health and throttling, cursor age, permission freshness, queue age/depth, stage duration/failures, indexing coverage, search latency, model usage/errors, citation failures, answer status, resource pressure, and cost estimates.

Operational logs exclude secrets and document/query contents by default. Diagnostics require explicit opt-in, access control, retention, and redaction. Aggregate telemetry is sufficient for most capacity recommendations.

## Health and overload

Separate liveness from readiness and dependency diagnostics. Apply bounded request queues, per-user/tenant limits, deadlines, circuit breakers, and graceful degradation. Interactive capacity is reserved separately from bulk ingestion. A model outage or full queue must return actionable errors, not hang indefinitely.

## Recovery

Back up PostgreSQL, artifact storage, encryption key material through secure independent procedures, configuration, and deletion/revocation records. Derived indexes may be rebuilt or snapshotted. Define and measure recovery point/time objectives for the chosen deployment before release.

A restore drill must recreate a usable system, replay deletion/revocation state, verify permissions and citations, and record duration. Backups are encrypted and access-limited; expired backup copies follow retention. Do not promise immediate erasure from immutable backups.

## Administration

Provide job inspection, bounded replay, cancellation, dead-letter handling, safe index rebuild, connector reconnect/disconnect, credential rotation, retention purge, and migration status. Audit administrative actions. Avoid broad destructive actions without a concrete impact preview.

## Costs

Track actual provider usage where returned, estimate missing usage explicitly, and associate costs with tenant/jobs/query runs without exposing content. Enforce token/request/job budgets and maximum capacity; billing estimates are advisory. Stop optional graph/OCR work at its configured budget boundary.

## Runbooks required before release

Source consent revoked; expired delta cursor; model quota exhaustion; queue backlog; parser crash loop; search disk watermark; stale permissions; failed migration; accidental secret disclosure; backup restore; and full single-node failure.

Publish a supported-version matrix, upgrade procedure, known limitations, and benchmark methodology. Health dashboards do not substitute for tested recovery.
