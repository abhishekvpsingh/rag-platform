# Architecture

## Selected baseline

| Concern | Initial choice |
|---|---|
| Web | Next.js, TypeScript, accessible component primitives, Tailwind CSS |
| API | Python 3.12, FastAPI, Pydantic |
| Metadata | PostgreSQL with SQLAlchemy and Alembic |
| Search | OpenSearch keyword and vector search, behind a retrieval adapter |
| Jobs | Celery workers with RabbitMQ, durable queues, publisher confirms, late acknowledgment, and database-backed job state |
| Artifacts | Local persistent volume initially, S3-compatible adapter for distributed operation |
| Models | Provider adapters; initial OpenAI-compatible text/embedding integration and deterministic test doubles |
| Deployment | Docker Compose; Kubernetes after local contracts are stable |

These are accepted implementation defaults. The API/web foundation is implemented first; stateful services and adapters arrive in later tasks. Consult PROGRESS.md for actual implementation status. Benchmark OpenSearch permission filtering and hybrid retrieval before claiming production capacity. Do not introduce a second vector backend without evidence and a decision record.

## Boundaries and data flow

API authenticates requests, resolves tenant and source identities, validates configuration, and records durable jobs. A transactional outbox bridges metadata transactions and queue publishing. Workers discover, download, parse, version, chunk, embed, and index independently. Search indexes contain only committed searchable generations. Query services authorize, retrieve, rerank, resolve temporal applicability, and generate supported answers.

PostgreSQL is the authority for document identities, revisions, grants, jobs, and active index generations. Artifacts are durable processing inputs. Search and optional graph stores are rebuildable derived views. PostgreSQL is not a broker or high-volume analytics warehouse.

## Reliability contracts

Assume at-least-once delivery. Each stage uses deterministic job keys, unique constraints, bounded retries with jitter, leases/heartbeats where needed, and idempotent outputs. Use generation checks so old jobs cannot overwrite newer revisions or resurrect deleted content. Acknowledge broker messages after durable stage completion. Dead-letter failures remain visible and retryable.

Keep source permission state and content state independently versioned. Tombstone immediately on confirmed deletion or revocation; physical purge follows policy. Missing data from an incomplete listing is not proof of deletion.

## Deployment boundaries

Single-node services share the same contracts as distributed services. Worker code must not depend on process-local state or shared local paths; use artifact identifiers. Distributed mode requires shared object storage and externally reachable durable services. No application request provisions machines.

Separate interactive queries from ingestion queues and resource budgets. Keep synchronous APIs bounded; long operations return job IDs. Avoid holding database transactions open during provider or model calls.

## Extension points

Typed interfaces: SourceConnector, ArtifactStore, Parser, EmbeddingProvider, Reranker, GenerationProvider, SearchBackend, GraphBackend, and CapacityAdvisor. Version request/response schemas and capability declarations. Plugins run only from trusted installed code; uploading arbitrary executable plugins is outside scope.

## Failure behavior

A failed optional graph service falls back to authorized hybrid retrieval with visible degraded status. A failed authorization authority fails closed. Model outages return a clear error or an explicitly configured compatible fallback. Never mix embeddings from incompatible models. Provider rate limiting reduces concurrency rather than causing uncontrolled retries.

## Design validation

Verify outbox recovery, duplicate delivery, stale generation suppression, partial index builds, source permission revocation, and backup restoration before production release. See [data model](DATA_MODEL.md), [ingestion](INGESTION.md), and [evaluation](TESTING_AND_EVALUATION.md).
