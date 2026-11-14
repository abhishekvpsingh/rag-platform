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

## Implemented process health

`GET /health/live` reports process liveness. `GET /health/ready` returns 200 only when all five runtime dependency adapters (PostgreSQL, RabbitMQ, OpenSearch, artifacts, worker) are configured and pass bounded concurrent checks. Missing adapters return 503 with `not_configured`; failed or timed-out adapters return 503 with `unavailable`. Responses include dependency names/statuses and exclude connection URLs, credentials, and exception details. These public process endpoints do not establish tenant authorization or knowledge availability. The configured Compose entry point (`runtime_app --factory`) wires live adapters and fails startup on invalid settings. The lightweight `app` entry point remains explicitly unconfigured and returns `not_configured`. The worker probe performs a targeted broker round trip; TLS search validates its local CA and hostname.

## Long-running work

Return 202 with job ID for asynchronous ingestion, reindexing, graph construction, and migration. Support idempotency keys for duplicate-sensitive commands. Persist state before publishing queue events. Cancellation is cooperative and cannot undo already committed side effects.

## Answer streaming

Use SSE with explicit progress, evidence-ready, answer-delta, validation, completed, and error events. Include run/event IDs and define reconnection behavior. Authorization is checked before evidence or text is emitted. Streamed output is provisional until validation completes; unsupported output must be visibly marked and not persisted as a verified answer.

## Concurrency and compatibility

Settings use version/ETag preconditions. Define conflict errors and retry behavior. Additive changes preserve v1 clients; breaking changes need versioning and migration documentation. Generate frontend types from executable contracts where practical; Markdown documents behavior, not a duplicate hand-maintained schema.

## Acceptance

Contract tests cover errors, pagination, tenant isolation, idempotency, stale updates, streaming cancellation, and authorization on every resource including stored answers.

## Identity foundation routes

The explicitly enabled HTTPS identity API provides `POST /api/v1/auth/login`,
`GET /api/v1/auth/me`, and `POST /api/v1/auth/logout`. Tenant context is resolved
from persisted membership. Login returns a CSRF token; logout requires it in
`X-CSRF-Token`. Cookie flags, request Origin policy, setup, limitations and
operator commands are defined in [identity runtime setup](../rag-platform/infra/IDENTITY.md).
Owner bootstrap is local-only and has no HTTP route.
