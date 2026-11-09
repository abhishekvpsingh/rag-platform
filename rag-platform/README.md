# RAG Platform application

This directory is reserved for the application and its runtime assets. **No runnable application exists yet.** See the [project overview](../README.md) for capabilities and status.

## Planned layout

| Directory | Responsibility |
|---|---|
| `apps/web/` | Next.js web application and design system |
| `services/api/` | FastAPI application, authorization, APIs, and migrations |
| `services/workers/` | Connector, parsing, embedding, indexing, and evaluation jobs |
| `packages/` | Shared contracts, provider adapters, connectors, and retrieval modules |
| `infra/` | Docker Compose first; local Kubernetes and production manifests later |
| `tests/` | Integration, security, evaluation, and end-to-end fixtures |

## Runtime documentation requirements

When the first runtime is implemented, replace this section with verified prerequisites, supported versions, exact install/start/stop commands, ports, first-admin bootstrap, OAuth setup, model configuration, persistent volumes, backups, and teardown instructions.

Keep credentials in ignored environment files or a secret manager. Keep customer documents and generated indexes outside source control. Starting local services must not provision paid cloud resources.

For development scope and acceptance criteria, use the [documentation index](../planning/INDEX.md).
