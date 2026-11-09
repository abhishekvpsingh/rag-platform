# Project progress

## Current state

T001 is complete and merged through [PR #2](https://github.com/abhishekvpsingh/rag-platform/pull/2). Mac local setup is verified. T002 has a first implementation increment for settings validation and readiness; Compose/runtime acceptance remains open. No storage connectors, authentication, ingestion, retrieval, or answers exist yet.

## Task status

| Task | Status | Evidence |
|---|---|---|
| T001 | Complete, merged | [Verification record](verification/T001.md), [PR #2](https://github.com/abhishekvpsingh/rag-platform/pull/2), merge `ada2f08` |
| T002 | In progress | [Verification checkpoint](verification/T002.md); settings/readiness implemented; Compose/runtime acceptance pending |
| T003–T025 | Not started | Specifications only |

## Development checkpoint

- Updated at: 2026-11-09T23:41:08Z.
- Session state: in-progress; first T002 increment and fixture remediation verified locally and saved remotely in draft PR #3.
- Active task: T002, development configuration and health contract. Still open: actual service adapters, remaining architecture adapter interfaces, Compose/images/volumes, Celery worker integration, startup/shutdown/recreation persistence tests, dependency recovery checks, and measured Mac stack resource use.
- Feature branch: feature/T002-runtime-contracts.
- Base main SHA: ada2f08a77377bc1968df942a64c37a47f941486; fetched and matches local main.
- Last confirmed pushed implementation/checkpoint: ccef1925fbe4fae9c16b0435af116fe82c68df2d on origin/feature/T002-runtime-contracts (remote SHA verified). These documentation-only notes follow it; resolve the latest branch head from Git/GitHub on resume.
- Confirmed remote PR: [T001 PR #2](https://github.com/abhishekvpsingh/rag-platform/pull/2), head eb7b97536e71d87601d2882586b1fbba5ef405aa merged 2026-11-09T20:50:26Z as ada2f08; final-head Documentation, Backend, Frontend, CI Gate, and GitGuardian passed. [T002 draft PR #3](https://github.com/abhishekvpsingh/rag-platform/pull/3) confirmed open/draft; implementation and remediation pushed through ccef192.
- Changed files: API runtime/readiness modules, API endpoint wiring, configuration/health tests, application/infra README, API contract spec, T001/T002 verification records, this checkpoint. No dependency/lockfile changes or unrelated edits.
- Completed steps: reconciled T001 merge; created task branch from latest origin/main; installed isolated Node 22.23.4, pnpm 10.34.9, uv 0.13.5 and uv-managed Python 3.12.14. Activation: `source "$HOME/.local/share/rag-platform/env.sh"`. Conda Python 3.12.4, Homebrew Node 26.4.0, existing uv 0.9.26, and shell startup files preserved and rechecked. Playwright's automatic cleanup initially removed an older headless browser cache; restored build 1148 with GC disabled and documented the preservation option.
- Implementation: side-effect-free runtime settings validation with redacted errors; typed DependencyProbe and bounded concurrent readiness orchestration; `/health/ready` truthfully returns 503/not_configured until all five live adapters exist. No feature/authorization claims changed.
- Exact checks on T001 merge before edits: frozen uv/pnpm installs; backend lint/format/mypy and 3 tests; docs 35/0; frontend format/lint/types, 1 unit test, build, Chromium install, 2 desktop/mobile tests all passed. See [T001 evidence](verification/T001.md).
- Exact checks on T002 working tree: `uv sync --frozen`, Ruff check/format (15 files), mypy (8 sources), pytest (33 passed), docs (36 files, 0 errors), and `git diff --check` passed. Configuration CLI exited 1 as expected with only missing names; synthetic success/failure CLI paths pass in tests. Lockfiles unchanged. Actual HTTP: live 200, ready 503/not_configured, web 200. See [T002 evidence](verification/T002.md).
- Running operations: web production preview via `pnpm --filter @rag-platform/web start --port 3000`, PTY session 15000; updated uvicorn API loopback port 8000, process 53033 / PTY session 38139. Started and HTTP verified, intentionally left running for owner preview. Output is in tool session streams, not committed logs; these transient sessions are not a durable service manager. Docker Desktop running (engine 27.3.1 / Compose 2.30.3); no T002 containers launched.
- Mac environment: Intel, macOS 26.6.2, 16 logical CPUs, 16 GiB RAM; Docker VM capacity 16 CPUs / 8,218,132,480 bytes RAM. This is capacity inspection, not stack usage measurement.
- CI: initial checkpoint Actions runs 42722019556 (push) and 42722056757 (PR) passed all four Actions jobs at df9d5a5; this follow-up requires its own checks. GitGuardian flagged a literal synthetic test URL in df9d5a5 (incident 39882436). No real account/service used it. Follow-up replaces embedded test credentials with ephemeral generated values; security scanning stays enabled and history is preserved. At ccef192 the scanner still flags only that original df9d5a5 occurrence, not a new fixture credential. Owner classification of synthetic incident 39882436 in GitGuardian is needed; dashboard access is not available through the connected tools. Actions runs 42722342476/42722351516 were pending at last inspection; inspect their final results and any newer documentation-head runs. No merge allowed with a failed check.
- Blockers: no implementation blocker for the next T002 step; security-check status must be resolved before any eventual merge. Sandbox restrictions require reviewed elevated commands for network, Git metadata, Docker, and user-directory tool/cache writes. No secrets requested or committed.
- Next action: inspect the latest PR #3 head/checks and this checkpoint, then implement the private, authenticated Compose stack and real readiness adapters. Use the settings contract in `rag-platform/infra/README.md`, verifying actual service behavior before documenting runtime commands.
- Risks/limitations: T002 acceptance incomplete; draft must not merge even if foundation CI passes. Live dependency, persistence, security connection configuration, and Mac stack resource tests remain unverified.

## External prerequisites and limitations

OAuth apps/test accounts and model credentials are required for later live tests. License/private reporting decisions precede a software release. Cloud choice/account/budget precedes T024. None blocks foundation development.

Main protection status remains unverified; native auto-merge was disabled in earlier metadata. Exact admin steps are in the application README. No repository controls were changed in this session.

Never ask for secrets in chat. Do not infer production readiness from foundation tests. Follow [continuity](DEVELOPMENT_CONTINUITY.md) and [GitHub workflow](GITHUB_WORKFLOW.md).
