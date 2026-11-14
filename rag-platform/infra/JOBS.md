# Durable background work

PostgreSQL owns job state. RabbitMQ delivers opaque tenant/job IDs to Celery.
The transactional outbox inserts the job and its initial message in the same
transaction, so a broker outage cannot lose a committed job. A separate dispatcher
publishes persistent messages with publisher confirms and bounded network calls.
No raw source content, credentials or arbitrary executable payload is queued.

## Start and migration

After building the updated API image, run migrations with the configured secret
environment (see [identity setup](IDENTITY.md)):

```bash
docker compose exec api alembic upgrade head
docker compose --profile jobs up -d dispatcher
```

The worker consumes `runtime` and `maintenance`. The opt-in `jobs` profile adds
the dispatcher, avoiding an implicit database migration or background job start
in an existing installation. Workers have late acknowledgments, worker-loss
redelivery and prefetch one. Ingestion handlers/queues arrive with T007.

The initial installed handler is `worker_check`, version `worker-check-v1`: a
bounded diagnostic that runs for 0–60 seconds, heartbeats and publishes a durable
completion record. It performs no document ingestion or model calls. New handlers
must be installed trusted code, persist processing versions, use bounded calls
and cooperate with lease/cancellation checks before external side effects.

## Authenticated APIs and Operations view

Enable identity APIs with the existing HTTPS setup. Cookie-authenticated mutation
requests require the exact configured Origin and `X-CSRF-Token` from login.

- `POST /api/v1/jobs/checks`, JSON `duration_seconds` (0–60), with
  `Idempotency-Key` (1–128 characters): returns 202 and the persisted job. Only
  owners/admins can submit diagnostic work. Reusing a key with different input
  returns 409. Up to 100 nonterminal jobs per owner are allowed.
- `GET /api/v1/jobs`: latest 50 jobs owned by the current user in their tenant.
  Admin membership does not expose another user's jobs. No payloads/lease tokens
  appear in the response.
- `POST /api/v1/jobs/{id}/cancel`: stops future progress/publication; cancellation
  is cooperative and does not undo a previously committed result.
- `POST /api/v1/jobs/{id}/replay`: owner/admin can replay their failed job only
  while the target generation remains valid. Attempts/history are preserved.

The Operations view polls every five seconds through the server-side `/api/jobs`
proxy. Set `RAG_INTERNAL_API_URL` to the API's trusted internal origin; Compose
sets `http://api:8000`. It forwards only the session cookie, disables caching,
bounds the fetch, rejects redirects and filters internal fields. Route both web
and the authentication API under the same HTTPS browser origin so the host-only
session cookie applies. Without an authenticated session it shows a sign-in
requirement; sign-in forms are still future work. There are no fake job rows.
On failed refresh/revocation, previously displayed job details are removed.

## Failure and lifecycle rules

A worker owns a random lease token for 30 seconds. Heartbeats renew it; expired
or replaced tokens cannot publish. Progress is monotonic within a job. Three
execution attempts are allowed with exponential delay plus jitter for transient
failure; permanent failures stop immediately. Explicit replay can grant up to
two additional attempts, with a lifetime ceiling of five.

The dispatcher scans at most 100 candidates per batch. Failed publishing retries
with a capped delay (at most 60 seconds); ten failed attempts abandon that outbox
event and mark an undispatched job failed. Pending events are not duplicated by
the recovery sweep. Missing deliveries after a confirmed publish are re-enqueued
after 60 seconds; expired worker leases are recovered. Duplicate delivery is
expected and safe. Publishing successfully and crashing before marking the
outbox sent can produce a duplicate, never a second visible result.

Publication atomically records one immutable result and activates the target's
current generation. Generation changes, tombstones, account/membership revocation
and cancellation reject obsolete work. Invalidation removes the active pointer;
historical records remain for audit. Future source deletion must call this
lifecycle boundary in the same authoritative source-state transaction; it must
also hide/remove search and artifact access in their own adapters. T006 does not
claim those later adapters exist.

## Verification and operational limits

```bash
PYTHONPATH=services/api/src uv run --frozen python scripts/verify_identity.py
```

This creates disposable PostgreSQL and RabbitMQ containers and a real local
Celery process. Tests include concurrent submission/claims, duplicate messages,
broker stop/restart, killing an active worker, stale-generation/tombstone
publication rejection, cancellation and migration/restore. Only created test
containers/processes are removed. The process-kill exercise uses Celery's solo
pool; Compose uses its normal prefork worker. Linux CI also verifies the Compose
runtime. This is single-machine recovery evidence, not cluster-scale validation.

Upgrade adds empty job tables without backfill. Back up before upgrading; do not
downgrade a populated job database because that drops job history. Recover a
failed upgrade from a tested encrypted backup. After a restore, the dispatcher
replays pending events/expired leases; document tombstone replay and full release
recovery remain later work. Job/audit retention and an administrative attempt
history UI are future operational work.
