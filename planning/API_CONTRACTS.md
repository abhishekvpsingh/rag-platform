# API contracts

## Conventions

Use `/api/v1`, generated OpenAPI, typed request/response schemas, opaque IDs, UTC timestamps with explicit tenant-timezone handling, cursor pagination, bounded page sizes, and stable error codes. Validate all input server-side. Tenant/user context is derived from authentication and membership.

Error envelope: `code`, safe `message`, `request_id`, optional field errors and retry metadata. Never include provider tokens, raw stack traces, or unauthorized resource existence. Use 401 for unauthenticated requests and consistent 403/404 policy for unauthorized resources.

## Resource groups

| Resource | Required operations |
|---|---|
| Session/bootstrap | One-time owner creation, login/session state, logout |
| Connections | Supported capabilities, OAuth start/callback, list, test, reconnect, disconnect |
| Sync/jobs | Start, status, bounded list, cancel, retry |
| Documents | Authorized list/detail, revisions, preview, source link |
| Questions | Submit, stream events, result, citations, feedback |
| Policy review | Authorized assertions/conflicts, reviewed resolution |
| Settings | Redacted read, validated versioned update, impact preview |
| Evaluations | Dataset/run metadata, start, results |
| Recommendations | Evidence, dismiss/snooze, activation/migration preview |
| Operations | Health, readiness, authorized metrics, backup/migration status |

## Long-running work

Return 202 with job ID for asynchronous ingestion, reindexing, graph construction, and migration. Support idempotency keys for duplicate-sensitive commands. Persist state before publishing queue events. Cancellation is cooperative and cannot undo already committed side effects.

## Answer streaming

Use SSE with explicit progress, evidence-ready, answer-delta, validation, completed, and error events. Include run/event IDs and define reconnection behavior. Authorization is checked before evidence or text is emitted. Streamed output is provisional until validation completes; unsupported output must be visibly marked and not persisted as a verified answer.

## Concurrency and compatibility

Settings use version/ETag preconditions. Define conflict errors and retry behavior. Additive changes preserve v1 clients; breaking changes need versioning and migration documentation. Generate frontend types from executable contracts where practical; Markdown documents behavior, not a duplicate hand-maintained schema.

## Acceptance

Contract tests cover errors, pagination, tenant isolation, idempotency, stale updates, streaming cancellation, and authorization on every resource including stored answers.
