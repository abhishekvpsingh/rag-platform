# Implementation plan

## Execution rules

Work in the order below unless independent tasks or a documented dependency justify another order. Each task requires code/artifacts, meaningful verification, relevant documentation updates, and a PROGRESS entry. A milestone is complete only when its acceptance criteria pass. Keep optional capabilities disabled until verified.

Do not build every feature simultaneously. The first useful target is an end-to-end, owner-only, permission-safe answer from a real supported source. Multi-user sharing requires explicit ACL support; it cannot be approximated by granting everyone connector-owner access.

## M0 — Repository and measurable contracts

### T001 — Bootstrap application workspace

Dependencies: none. Create the planned application directories, Python/TypeScript workspace configuration, lockfiles, lint/typecheck/test tools, and CI. Keep all runtime assets under `rag-platform/`.

Acceptance: fresh dependency installation succeeds with pinned tool versions; API/web smoke tests run; exact verified commands are documented. CI requires no company credentials.

### T002 — Runtime and contracts

Dependencies: T001. Implement Compose for PostgreSQL, RabbitMQ, OpenSearch, artifact volume, API, web, and workers. Add health checks, development configuration validation, explicit ports, persistent volumes, and typed adapter contracts.

Acceptance: clean startup/shutdown and restart preserve state; dependency readiness is visible; no public management-port exposure by default. Document actual Mac resource use.

### T003 — Evaluation baseline and decision records

Dependencies: T001. Create synthetic policy/access/dataset fixtures, evaluation schema, baseline harness, and initial measurable workload. Confirm library compatibility and capture consequential changes in decision records.

Acceptance: deterministic fixture runner works offline; expected citations/forbidden sources are encoded; initial workload-specific quality and latency targets are recorded before tuning. Owner licensing decision remains tracked without blocking coding.

## M1 — Secure foundation and web shell

### T004 — Identity, persistence, and secrets

Dependencies: T002. Implement migrations, one-time owner bootstrap, secure sessions, tenant-scoped repositories, secret encryption, source identity mappings, audit events, and authorization interfaces.

Acceptance: cross-tenant fixtures pass; bootstrap cannot be reused; secrets are redacted; migration and restore smoke tests pass. Source ownership does not grant another user access.

### T005 — Web design system and navigation

Dependencies: T001. Build design tokens, accessible components, responsive shell, Ask/Sources/Knowledge/Operations/Settings screens, and honest empty/error states.

Acceptance: browser checks cover keyboard navigation and narrow/wide layouts. No fake functional controls or unlabeled demo metrics.

### T006 — Durable work engine

Dependencies: T004. Implement jobs, attempts, transactional outbox, queue routing, idempotency, bounded retries, heartbeats/cancellation, and generation/tombstone rules.

Acceptance: duplicate delivery and worker-kill tests recover without duplicate visible outputs; failed publication is replayed; stale work cannot resurrect a deletion. Job status appears in the UI.

## M2 — Real connected ingestion

### T007 — Parser and indexing pipeline

Dependencies: T003, T006. Implement initial supported parsers, artifacts, revisions, structure-aware chunks, model adapters, embedding batches, OpenSearch mappings, and generation publication. Include dataset schema/header summaries but no unimplemented aggregation claims.

Acceptance: synthetic file corpus indexes with exact locators; malicious/unsupported/oversized files receive bounded failures; unchanged content avoids redundant work; provider errors are recoverable.

### T008 — Google Drive My Drive

Dependencies: T004, T006, T007. Implement OAuth, folder selection, native document export, paginated discovery, incremental changes, permission/owner-only gating, and reconnect/disconnect.

Acceptance: contract tests pass and opt-in live tests demonstrate ingestion, edits, deletion, revocation behavior, cursor reset, and reconnect with a supported account. Without credentials, mark live validation blocked, not complete.

### T009 — Personal OneDrive

Dependencies: T004, T006, T007. Implement delegated OAuth, drive/item identity, delta sync, short-lived downloads, scope selection, permission/owner-only gating, and reconnect/disconnect.

Acceptance: equivalent live/contract evidence to T008; expired delta link and moved/deleted items are tested. Do not label work/school OneDrive supported yet.

### T010 — Source operations experience

Dependencies: T005, T008, T009. Complete onboarding, connection capability matrix, progress/coverage, file failures, retry/cancel, freshness, and scope/disconnect previews.

Acceptance: full supported source onboarding works in a browser; partial ingestion and authorization staleness are visible without leaking unauthorized metadata.

## M3 — Grounded and current answers

### T011 — Authorized hybrid retrieval

Dependencies: T003, T007, T004. Implement keyword/vector fusion, bounded parent retrieval, provider-backed reranking, authorization checks, and evaluation reporting.

Acceptance: held-out retrieval targets pass; exact identifiers and semantic queries work; forbidden evidence is excluded before model transmission. Measure permission-filter performance.

### T012 — Answer generation and citations

Dependencies: T011, T005. Implement query/run APIs, SSE, grounded generation, claim-linked citations, evidence previews, feedback, abstention, and access-aware history/cache behavior.

Acceptance: real supported-source question produces inspectable evidence; unanswerable and injection cases behave correctly; revoked citations/history are inaccessible. Stream errors and cancellation are tested.

### T013 — Temporal policy resolution

Dependencies: T012. Implement effective intervals, status/authority/scope rules, historical queries, supersession, conflict states, review workflow, and short historical suggestions.

Acceptance: all deterministic temporal fixtures pass; reupload and future-effective traps do not select the wrong policy; unresolved conflicts are visible with authorized evidence.

### T014 — First runnable release verification

Dependencies: T010, T013. Run live connector tests, browser workflows, security fixtures, workload evaluation, and a single-node backup/restore drill. Publish exact installation instructions and limitations.

Acceptance: end-to-end release criteria pass for the declared supported scope. License selection and private security reporting channel must be resolved before publishing a software release; unaffected development may continue.

## M4 — Data breadth and operational controls

### T015 — Controlled structured analytics

Dependencies: T012. Implement isolated read-only DuckDB execution, schema/locale handling, analytical query planning, resource limits, and result provenance.

Acceptance: numerical fixtures pass exactly; unauthorized joins and filesystem/network escape attempts fail; source revisions are cited.

### T016 — OCR and robust extraction

Dependencies: T007. Add OCR adapter, language/page controls, extraction confidence, budgets, and partial-parse review.

Acceptance: scanned fixtures produce page-citable text; poor OCR is visible; resource exhaustion is contained.

### T017 — Settings, budgets, and operations

Dependencies: T014. Complete versioned configuration, model tests, impact previews, reindex cutovers, cost accounting, retention/purge, metrics/traces, audit UI, and operational runbooks.

Acceptance: model changes cannot mix embedding spaces; budgets cap work; restored data honors deletion state; settings enforce administrator permissions.

## M5 — Enterprise access and recommendations

### T018 — Organizational account support

Dependencies: T014. Add Google shared drives and Microsoft 365 work/school OneDrive with explicit capability matrices, organizational identity/group mapping, and tested inherited grants. Add OIDC/SSO integration.

Acceptance: live supported enterprise account tests pass; unresolved groups/ACLs fail closed; revocation staleness is measured. SharePoint remains a separate future connector.

### T019 — Evidence-based capacity and graph advisor

Dependencies: T017. Implement local aggregate telemetry, minimum-sample windows, bottleneck classification, bounded trial proposals, cost estimates, dismiss/snooze, and administrator activation flow.

Acceptance: known workloads generate appropriate recommendations; source/model throttling does not cause blind machine recommendations; no automatic activation or cloud provisioning occurs.

## M6 — Optional graph retrieval

### T020 — Graph build and lifecycle

Dependencies: T013, T017, T019. Select backend through a decision record; implement evidence-backed graph schema, bounded extraction, entity resolution, access enforcement, incremental refresh, deletion, and coverage UI.

Acceptance: graph stays off by default; trial/build can resume/cancel; restricted evidence cannot leak through entities or paths; costs remain bounded.

### T021 — Graph-assisted query evaluation

Dependencies: T020. Add selective graph traversal to query planning, quality comparison, fallback, and graph exploration UI.

Acceptance: relationship-task improvements are measured against baseline, ordinary retrieval does not regress beyond accepted tolerance, outage fallback and deactivation work.

## M7 — Distributed deployment

### T022 — Local multi-node profile

Dependencies: T017. Add kind/k3d profile, shared artifact adapter, externalized services, worker resource declarations, graceful draining, and failure tests.

Acceptance: simulated nodes schedule multiple workers and recover interrupted work; all limitations and actual resource needs are documented.

### T023 — Production cluster deployment and migration

Dependencies: T022, T019. Add Helm/manifests, pool limits, workload autoscaling, infrastructure autoscaler integration guidance, TLS/secrets/storage controls, and checkpointed single-to-cluster migration.

Acceptance: small real cluster demonstrates scale-out/in, bounded machine ceilings, workload isolation, recovery, migration validation, and rollback with deletion/revocation safety. Stateful services have separate procedures.

### T024 — Guided cloud provisioning

Dependencies: T023 and owner cloud-provider choice. Deliver reviewed infrastructure templates for one supported provider, preflight/plan UI, cost estimate, and explicit administrator execution.

Acceptance: a disposable authorized cloud environment is provisioned and destroyed reproducibly; no credentials are stored in Git; no provisioning happens merely from accepting an advisor notification.

## M8 — Production release hardening

### T025 — Release readiness

Dependencies: T015–T024 for the full final-product release. Run security review, load/fault benchmarks, recovery drills, accessibility verification, dependency/license checks, and documentation review.

Acceptance: publish supported configurations, measured limits, SLOs/RPO/RTO, known issues, upgrade/rollback instructions, release artifacts and compatibility matrix. Do not claim billion-file scale from extrapolation alone.
