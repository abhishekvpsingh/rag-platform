# Testing and evaluation

## Layers

- Unit tests for nontrivial policy resolution, chunk locators, permission mapping, configuration validation, and job-generation rules.
- Adapter contract tests for providers, connectors, parsers, search, and optional graph backends.
- Integration tests against real local PostgreSQL, RabbitMQ, OpenSearch, and artifact storage.
- Browser end-to-end tests for core user journeys and accessible UI states.
- Opt-in live connector tests with dedicated accounts and synthetic files; never require credentials for ordinary CI.
- Offline retrieval/answer evaluation with versioned datasets and a benchmark harness.
- Fault/load/recovery tests for release milestones.

Do not add tests that merely mirror constants or mock away the behavior under test. External models are nondeterministic; separate deterministic correctness fixtures from statistically evaluated answer quality.

## Required datasets

Synthetic company policy corpus with current, old, future, conflicting, scoped, restricted, deleted, and partially superseded documents. Include exact-match identifiers, one relevant passage among distractors, long documents, tables, multilingual text, unanswerable questions, prompt injections, corrupt files, and structured numerical tasks.

Every question has authorized identity/scope, expected evidence, as-of date, expected answer behavior, and forbidden evidence. Keep held-out questions separate from tuning examples. Record corpus, model, index, prompt, and settings versions.

## Metrics and gates

| Area | Required measurement |
|---|---|
| Retrieval | Recall@k, ranking quality, permission-filter effect |
| Answers | Claim support, citation precision/coverage, correctness, abstention |
| Temporal | Current/historical applicability and conflict handling |
| Security | Cross-tenant/access leaks; all deterministic isolation fixtures must pass |
| Freshness | Content/update/deletion/revocation propagation latency |
| Operations | Queue throughput, p50/p95 latency, errors, recovery time, cost |
| Graph | Baseline versus graph-assisted quality and resource cost |

Hard deterministic security and policy fixtures must pass completely. Establish numeric quality/latency targets in M0 using a declared workload and hardware; do not invent universal production thresholds. Changes must not regress accepted held-out metrics beyond documented tolerance.

## Fault scenarios

Duplicate delivery, worker kill mid-stage, expired lease, broker outage, failed publish after database commit, stale job after deletion, invalid cursor, permission revocation mid-query, partial index build, model timeout, API throttling, storage exhaustion, and restore from backup.

## Reporting

CI reports exact checks and artifacts. Benchmark reports disclose corpus size, chunks, ACL distribution, hardware, models, concurrency, cold/warm cache, percentile latency, throughput, and cost. Simulated local nodes do not certify production resilience. Release notes distinguish fixtures, live integrations, and untested account/provider combinations.

## Implemented offline baseline (T003)

The [fixture workload](../rag-platform/tests/fixtures/evaluation/README.md) declares
45 synthetic evidence documents and 17 cases (5 tuning / 12 held out), with exact
revisions/locators, explicit forbidden evidence and expected answer behaviors.
The executable schema and independent scorer live in
`rag-platform/services/api/src/rag_api/evaluation.py`. Corpus/split and runner
SHA-256 values identify the report inputs; baseline/processing/model/index/prompt
versions are explicit. No model/index/prompt is used in the reference run.

Initial targets were fixed before the first run: Recall@3 >= 0.90, zero forbidden
or invalid citations, and warm serial p95 <= 50 ms per held-out split (100 samples)
on the owner's Intel Mac. CI enforces quality/access/citation gates and offline
regression tests, not wall-clock timing. [Decision 0001](decisions/0001-offline-evaluation-baseline.md)
records scope and alternatives. This reference fixture baseline does not validate
product retrieval, answer correctness, prompt injection resistance, or live ACLs.
