# ADR 0005: Durable work authority and fenced publication

- Status: accepted for T006.
- Context: at-least-once broker delivery, worker termination and source deletion
  must not duplicate visible outputs or resurrect obsolete work.
- Decision: PostgreSQL owns jobs, immutable attempt records, leases, targets and
  generation visibility. A transactional outbox bridges database commit and
  confirmed RabbitMQ publication. A separate opt-in dispatcher scans bounded
  batches and recovers lost deliveries/leases. Celery transports opaque IDs and
  executes only installed versioned handlers. No Celery result backend is used.
- Publication: job and target rows are locked, a current lease and generation are
  required, and result plus active generation commit atomically. Cancellation,
  membership revocation and tombstones fail closed. External side effects will
  require adapter-specific idempotency before future handlers are accepted.
- Retry: capped execution attempts and jittered delay; capped publisher failures
  with visible failure state; explicit replay preserves history and has a total
  attempt ceiling. Source-owner privacy applies to job status and operations.
- Alternatives: publishing directly from API requests can strand committed work;
  broker-only result state cannot fence old workers or atomic database cutover;
  pretending the diagnostic task ingests files would misstate product capability.
- Consequences: database migrations and the jobs dispatcher must be explicitly
  enabled. A trusted internal web proxy exposes owner-scoped status only through
  authenticated sessions. No paid resources or external provider accounts.
- Validation: real PostgreSQL concurrency, RabbitMQ outage, worker kill, duplicate
  publication and deletion/cancellation tests; UI fixtures separately exercise
  status transitions. PROGRESS tracks completed evidence.
