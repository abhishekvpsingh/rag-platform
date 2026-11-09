# Documentation index

## Start here

1. [Product](PRODUCT.md): scope, roles, invariants, and release expectations.
2. [Architecture](ARCHITECTURE.md): chosen components and contracts.
3. [Implementation plan](IMPLEMENTATION_PLAN.md): ordered tasks and acceptance criteria.
4. [Continuity](DEVELOPMENT_CONTINUITY.md): checkpoint and resume protocol.
5. [GitHub workflow](GITHUB_WORKFLOW.md): feature branches, automatic pushes, and verified merges.
6. [Progress](PROGRESS.md): current status, active checkpoint, and next work.

## Read by task

| Work | Specifications |
|---|---|
| Data and jobs | [Data model](DATA_MODEL.md), [ingestion](INGESTION.md) |
| Sources | [Connectors](CONNECTORS.md), [security](SECURITY_AND_PERMISSIONS.md) |
| Answers | [Retrieval](RETRIEVAL_AND_ANSWERS.md), [temporal knowledge](TEMPORAL_KNOWLEDGE.md) |
| Tables | [Structured data](STRUCTURED_DATA.md) |
| Providers and settings | [Models/configuration](MODELS_AND_CONFIGURATION.md) |
| Frontend | [UI/UX](UI_UX.md), [API contracts](API_CONTRACTS.md) |
| Optional graph | [Knowledge graph](KNOWLEDGE_GRAPH.md) |
| Infrastructure | [Deployment/scaling](DEPLOYMENT_AND_SCALING.md), [operations](OPERATIONS.md) |
| Verification | [Testing/evaluation](TESTING_AND_EVALUATION.md) |
| Rationale | [Decision records](decisions/README.md) |

## Authority and maintenance

Explicit owner instructions take precedence. Product invariants and security requirements constrain implementation. Accepted decision records explain technology decisions; current specifications define intended behavior. If documents conflict materially, resolve the conflict and record the decision before implementing affected behavior. Do not interpret a roadmap item as an implemented capability.

Application README and executable schemas/commands must remain accurate. Preserve one source of truth: task definitions in IMPLEMENTATION_PLAN, status in PROGRESS, interface schema in code, and architectural rationale in decision records.
