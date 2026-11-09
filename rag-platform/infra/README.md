# Development runtime contract

T002 is in progress. Configuration validation and dependency health orchestration are implemented; Compose, service adapters, containers, and persistence verification remain pending. There is no runnable Compose stack yet.

## Validate configuration

From `rag-platform/`, with the pinned toolchain active and settings supplied through your local shell or secrets tooling:

```bash
PYTHONPATH=services/api/src uv run --frozen python -m rag_api.runtime
```

Exit 0 means the configuration is syntactically valid, **not** that services are reachable. Exit 1 lists invalid/missing variable names without input values. The validator does not load `.env` implicitly, create directories, contact services, or start workers. Do not put real credentials in command history or committed files.

| Setting | Contract |
|---|---|
| `RAG_DATABASE_URL` | PostgreSQL URL with username, password, host, and database path; no query/fragment |
| `RAG_BROKER_URL` | AMQP/AMQPS URL with username, password, host, and vhost path; no query/fragment |
| `RAG_SEARCH_URL` | HTTP/HTTPS origin; credentials are separate; no query/fragment |
| `RAG_SEARCH_USERNAME`, `RAG_SEARCH_PASSWORD` | Required nonempty server-side credentials |
| `RAG_ARTIFACT_ROOT` | Absolute path other than `/`, with no `..` components; existence/access checked by the future artifact adapter |
| `RAG_PROBE_TIMEOUT_SECONDS` | Finite per-probe deadline, 0.1–10 seconds; default 2 |
| `RAG_WORKER_CONCURRENCY` | Integer 1–4; default 1 |
| `RAG_API_PORT`, `RAG_WEB_PORT` | Distinct integer ports 1024–65535; defaults 8000 and 3000 |
| `RAG_BIND_HOST` | Development host publishing must use `127.0.0.1` |

This is a development contract. It does not validate production TLS, source authorization, certificate trust, secret strength, or network policy. Internal container listener addresses will be distinct from host port publication. Runtime settings are not yet consumed by the foundation startup commands; those commands retain their documented ports.

## Health adapter contract

`rag_api.readiness.DependencyProbe` defines an asynchronous, non-mutating `check()` and a typed dependency name. `ReadinessChecker` requires PostgreSQL, RabbitMQ, OpenSearch, artifacts, and worker probes. It checks them concurrently under individual deadlines, cancels timed-out work, propagates request cancellation, rejects duplicate adapters, and redacts exception details. Adapters must release resources on cancellation. A readiness result is not a tenant authorization decision.

`create_app(readiness=...)` accepts a checker for runtime wiring. No checker with live service adapters is configured yet. The default `/health/ready` therefore returns 503 rather than reporting a running process as a working stack.

## Remaining T002 work

Implement pinned images/containers and Compose with private database/search/broker ports, persistent volumes, dependency health checks, artifact sharing, API/web, and bounded Celery workers. Add actual service probes, configure authenticated service access, and exercise unavailable/recovered dependencies. Verify clean startup/shutdown, state preservation across restart and container recreation, and Mac resource use. Record actual commands only after execution; Docker Desktop being available is not stack validation.
