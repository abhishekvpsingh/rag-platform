# Local development runtime

The default Compose project is `rag-platform-dev`. It runs PostgreSQL 17.6,
RabbitMQ 4.1.4, OpenSearch 3.9.0, the API, web, and one Celery worker. Docker
Desktop must be running. Use Python 3.12.14 and the pinned toolchain documented
in the [application README](../README.md).

From `rag-platform/`:

```bash
uv run --frozen python scripts/init_runtime.py
docker compose build
docker compose up -d --wait --wait-timeout 300
docker compose ps
curl --fail http://127.0.0.1:8000/health/ready
docker compose down --timeout 30
```

Setup refuses to overwrite `.env`. It creates random development credentials and
an independent local CA with one-year certificates under ignored `.data/tls`.
Keep both private. Do not run setup again against existing volumes to rotate
credentials: PostgreSQL/RabbitMQ/search initialize accounts only on first boot.
Rotation and production certificate management are later operational work.

Only API `127.0.0.1:8000` and web `127.0.0.1:3000` are published. If occupied,
prefix **every** Compose/verification invocation with `RAG_API_PORT=18000
RAG_WEB_PORT=13000` (on one line). No database, AMQP, search, or management port
is published. Container network listeners are separate from host publication.
Named volumes preserve database, broker messages, search data, and artifacts
across restart and `down`/`up`. Do not use `down -v` unless deliberately destroying
this development data. No real source data belongs in this unauthenticated
application foundation.

OpenSearch security remains enabled. Startup replaces demo certificates with
locally generated certificates, verifies hostname/CA trust, rejects unsafe demo
certificates, and removes demo users except the randomly configured admin.
The local admin is used only for development service probes. Production
least-privilege identities, backups, rotation, and deployment hardening remain
future work. The default network carries PostgreSQL and AMQP internally;
production deployment must add its own transport-security controls.

## Verification

After building, run the opt-in integration exercise:

```bash
uv run --frozen python scripts/verify_runtime.py
```

It writes clearly synthetic fixtures to a dedicated table, search index, queue,
and artifact; checks persistence across restart and full container recreation;
stops/restarts each dependency; verifies readiness fails while liveness stays up;
and checks actual published bindings. It leaves the development stack running
and volumes intact. `runtime_smoke.py` also checks unauthenticated search is
rejected and only the configured admin user exists. CI runs this exercise in a
fresh environment and requires **Runtime Integration** in **CI Gate**. Current
verification results and measured Mac usage are in [T002 evidence](../../planning/verification/T002.md).

## Configuration and adapters

The configured API entry point is `rag_api.main:runtime_app --factory`. It rejects
missing/invalid settings before serving. The lightweight `rag_api.main:app`
entry point intentionally remains unconfigured for UI-only development.

`RAG_DATABASE_URL` and `RAG_BROKER_URL` require authenticated PostgreSQL/AMQP
URLs. Search uses `RAG_SEARCH_URL`, `RAG_SEARCH_USERNAME`, `RAG_SEARCH_PASSWORD`,
and optional `RAG_SEARCH_CA` (otherwise system trust). `RAG_ARTIFACT_ROOT` must
be an absolute non-root directory without traversal. The configuration CLI
prints only invalid variable names, never values:

```bash
PYTHONPATH=services/api/src uv run --frozen python -m rag_api.runtime
```

The CLI consumes the process environment, not `.env`; Compose injects runtime
settings from `.env`. Validation does not connect to services. Probe timeout is
0.1–10 seconds (Compose uses 5); configured worker concurrency must be 1–4
(Compose fixes one process). API/web ports must be distinct, 1024–65535; the
host bind is always loopback.

`DependencyProbe` and `ReadinessChecker` provide bounded concurrent dependency
checks and redact connection exceptions. Worker checks use a targeted Celery
control round trip in a cancellable subprocess. Artifact readiness checks
existing directory access without mutating stored content; integration verifies
actual writes. `contracts.py` declares versioned typed extension boundaries
with tenant/source/revision/processing context. These interfaces do not
implement connectors, retrieval, authorization, models, graph, or provisioning.
