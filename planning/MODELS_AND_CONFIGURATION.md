# Models and configuration

## Configuration layers

Deployment bootstrap/secrets → versioned tenant settings → authorized user preferences. Define an executable schema with types, ranges, defaults, permission requirements, validation, and migration version. Environment variables configure bootstrap infrastructure, not an undocumented second settings system.

## Model interfaces

Generation: streaming, context limits, timeout, token usage, structured outputs capability. Embeddings: dimensions, normalization, tokenizer/length limits, batch limits, model revision. Reranking: candidate limits and score semantics. OCR: language, page limits, confidence and resource requirements.

Initial adapters target explicitly configured OpenAI-compatible endpoints and deterministic offline fixtures. Compatibility is tested per capability; do not assume every compatible endpoint implements all features. Local providers use the same adapters where possible and have no automatic external fallback.

## Administrator settings

| Category | Settings and consequences |
|---|---|
| Models | Provider, endpoint allowlist, model revision, secret reference, timeouts, rate/token budgets |
| Retrieval | Candidate limits, fusion, reranking, parent context, citation requirement, query decomposition budget |
| Ingestion | Folder scope, schedules, formats, OCR, concurrency, size limits, exclusions |
| Policies | Authority rules, scope mappings, review thresholds, timezone |
| Security | Identity configuration, session policy, authorization freshness, audit/log retention |
| Graph | Disabled default, corpus scope, extraction model, refresh budget, review requirements |
| Infrastructure | Mode, worker min/max, resource requests, pool sizes, supported storage settings |
| Recommendations | Enabled assessment, frequency, lookback, thresholds, notification preferences |

## Safe changes

Show validated impact before saving: immediate, restart required, reindex required, infrastructure migration, or additional data transmission/cost. Embedding model or dimensions require a new generation. Concurrency changes must respect deployment resource ceilings and provider quotas.

Use optimistic concurrency on settings updates, immutable audit versions, redacted reads, and a test-connection action that does not persist failed credentials. Never allow an ordinary member to change arbitrary endpoints, infrastructure, or secrets.

## Defaults

Single-node deployment, graph off, external calls only after provider configuration, bounded job concurrency, raw-content logging off, and no cloud provisioning. Assessment recommendations may run locally with explicit logging policy; activation and paid infrastructure remain opt-in. User-facing settings show understandable explanations and advanced controls progressively.
