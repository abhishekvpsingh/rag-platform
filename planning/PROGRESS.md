# Project progress

## Current state

T001 is complete and merged through [PR #2](https://github.com/abhishekvpsingh/rag-platform/pull/2). Mac local setup is verified. T002 runtime acceptance passes; merge is blocked on GitGuardian test-credential classification and final-head verification. No storage connectors, authentication, ingestion, retrieval, or answers exist yet.

## Task status

| Task | Status | Evidence |
|---|---|---|
| T001 | Complete, merged | [Verification record](verification/T001.md), [PR #2](https://github.com/abhishekvpsingh/rag-platform/pull/2), merge `ada2f08` |
| T002 | Runtime verified; merge blocked | [Verification evidence](verification/T002.md); GitGuardian classification pending |
| T003–T025 | Not started | Specifications only |

## Development checkpoint

- Updated at: 2026-11-10T16:09:26Z.
- Session state: blocked on GitGuardian classification access; runtime acceptance passes. Recovered final task-owned changes reviewed; backend lint/format/mypy, all 35 tests, docs and diff checks passed again. Publishing final fixes for current-head CI. PR remains draft, never bypass the failed security check.
- Active task: T002, runtime and contracts. Implementation/acceptance complete locally and fresh Linux CI at d1a7a7f; final-head CI and GitGuardian classification remain merge gates.
- Feature branch: feature/T002-runtime-contracts.
- Base main SHA: ada2f08a77377bc1968df942a64c37a47f941486; remote main unchanged.
- Last confirmed pushed commit: d1a7a7f0da4c53b7ba15bfa84f66a51d3310aec6. Final admin-certificate DN correction, safe error wording, and documentation follow it. Resolve current head from Git/PR rather than assuming this record's predecessor is latest.
- Remote PR: [T002 PR #3](https://github.com/abhishekvpsingh/rag-platform/pull/3), open/draft. T001 remains merged as ada2f08 via PR #2.
- Changed files: Compose/images/startup scripts, live health adapters, Celery runtime, typed extension contracts, runtime setup and persistence/security/recovery exercises, offline adapter tests, dependencies/uv lock, required Runtime Integration CI job, runtime/specification/verification documents. Task-owned changes only. Ignored local .env and .data/tls contain generated development secrets; never stage them.
- Completed steps: authenticated private stateful stack, loopback API/web, local CA/verified TLS, admin-only search initialization, persistent volumes, bounded probes and worker control round trip, typed extension interfaces. No product authorization or ingestion claims.
- Exact checks: Ruff check/format (24 files), mypy (17 sources), pytest (35), frontend format/lint/types/unit/build/browser (1 unit, 2 browser), docs (36/0), diff check passed. Final Mac runtime exercise passed at 01:35Z on d1a7a7f plus the final DN/error fixes: restart and full recreation preserve all four stores; each stopped dependency reports 503 while liveness stays 200, then recovers. Actual port binding, unauthenticated search rejection, and admin-only user assertions pass. See [T002 evidence](verification/T002.md).
- CI: d1a7a7f push/PR Documentation, Backend, Frontend, Runtime Integration, CI Gate all successful. Runtime jobs 129565403339/129565428106. GitGuardian 129565418717 fails original df9d5a5 fixture occurrence only. Final docs/fix head must be inspected independently; final-head evidence is recorded in PR #3 when checks finish.
- Running operations: scoped rag-platform-dev stack remains running with API 127.0.0.1:18000/web 127.0.0.1:13000 and named volumes. Existing lightweight previews on 8000/3000 were preserved. All build/download/verification subprocesses completed. Local logs under /private/tmp/rag-t002-*.log are diagnostic, not durable evidence. No external integration credentials used.
- Mac measurements: post-recovery six-container memory about 1.41 GiB; sample CPU 3.72% of one core, with multi-core recovery bursts. Docker VM has about 7.65 GiB available. See measured per-service values and limitations in T002 evidence.
- Blocker: GitGuardian dashboard requires browser sign-in; GitHub connector/CLI cannot classify that separate incident. Investigation demonstrates a configuration-only synthetic test credential, not a provisioned account. Supported action: incident 39882436 → Ignore → Test credential with evidence, then verify the PR scan. Owner sign-in/classification requested; no credentials requested in chat, no check override/history rewrite/scan suppression.
- Next action: inspect latest PR #3 checks; finish/confirm GitGuardian classification when dashboard access is available. Recheck current head, main compatibility, reviews/rules, then mark ready and squash merge with expected head only after every gate passes. No independent T002 implementation work remains. Continue independent T003 from origin/main while this external merge gate remains blocked.
- Risks/limitations: development runtime only; no source accounts/authentication/ingestion/answers/application-job idempotency. Startup TLS credentials are private local files, with documented rotation limitations. Never claim production validation from synthetic fixtures.

## External prerequisites and limitations

OAuth apps/test accounts and model credentials are required for later live tests. License/private reporting decisions precede a software release. Cloud choice/account/budget precedes T024. None blocks foundation development.

Main has no classic protection and no rulesets (verified 2026-11-10); native auto-merge was disabled in earlier metadata. Exact admin steps are in the application README. No repository controls were changed in this session.

Never ask for secrets in chat. Do not infer production readiness from foundation tests. Follow [continuity](DEVELOPMENT_CONTINUITY.md) and [GitHub workflow](GITHUB_WORKFLOW.md).
