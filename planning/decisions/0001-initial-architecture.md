# ADR 0001: Single-node foundation with distributed contracts

Status: accepted as implementation baseline; runtime validation pending.

## Context

The product must support accessible self-hosted installation, Google Drive and OneDrive ingestion, permission-aware current answers, and later graph/distributed capabilities. Initial development and testing occur on a Mac. There is no validated billion-file deployment.

## Decision

Use Next.js/TypeScript web, FastAPI/Python services, PostgreSQL metadata, RabbitMQ/Celery jobs, OpenSearch hybrid retrieval, and an artifact-store adapter. Start with Compose and local persistent artifacts. Adopt at-least-once jobs, a transactional outbox, immutable revisions, versioned processing, explicit authorization, and independently deployable worker pools.

Keep graph retrieval and distributed deployment off by default. Preserve graph interfaces without deploying an unused graph store. Use Kubernetes for the later multi-node path. Cloud provisioning is separate from application autoscaling and requires explicit administrator execution.

## Alternatives

A vector-only store simplifies initial integration but leaves exact-match and metadata retrieval concerns. Multiple search engines add operational cost before evidence justifies it. Spark/EMR can process large batches but does not replace an interactive retrieval service, source permission synchronization, or the full application control plane.

## Consequences

The local stack has a meaningful memory footprint and must be measured. OpenSearch filtered vector retrieval needs benchmarking. Celery delivery behavior requires explicit idempotency and durable state. Organizational connectors need more identity work than personal owner-only integrations.

## Validation

T002 validates local runtime resources; T003 defines evaluation; T006 validates fault recovery; T011 validates hybrid search and access filtering; T023 validates a real cluster. Revisit choices with measured evidence through a new decision record.
