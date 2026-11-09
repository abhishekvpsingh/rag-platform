# Project progress

## Current state

T001 foundation development in progress. Specifications remain the product contract. No source connectors or RAG answers are implemented.

## Task status

| Task | Status | Evidence |
|---|---|---|
| T001 | In progress | Runnable API/web foundation; local checks passing; final CI/recovery checks pending |
| T002–T025 | Not started | Specifications only |

## Development checkpoint

- Updated at: 2026-11-09 UTC.
- Session state: in-progress.
- Active task: T001, bootstrap and verify workspace/CI.
- Feature branch: feature/T001-workspace-foundation.
- Base main SHA: 468d5528d1cf885d4773c9a994a8b97cda9b699b.
- Last confirmed remote: feature branch created at base; first implementation checkpoint being prepared. Resolve actual head from Git/GitHub on resume.
- Changed files: Python API/tests, Next.js overview/tests, workspace/lockfiles, root CI/PR template, verified setup documentation. No customer data or credentials.
- Checks on working tree: uv sync --frozen and pnpm install --frozen-lockfile passed; Ruff/mypy passed; pytest 3 passed; frontend lint/typecheck passed; Vitest 1 passed; Next production build passed; Playwright desktop/mobile 2 passed; pnpm audit --prod found no known vulnerabilities. Final rerun after formatting/configuration updates pending.
- Running operations: none confirmed.
- Next action: push checkpoint/open PR, run final CI and local checks, validate fresh-workspace recovery, inspect screenshots.
- Acceptance still open: fresh install, API/web smoke checks, CI PR checks, resume exercise, merge-setting status.

## External prerequisites

OAuth apps/test accounts and model credentials are needed for later live tests, not foundation development. License selection/private reporting channel precede software release. Cloud choice/account/budget precede T024. GitHub merge settings must be recorded honestly if admin tooling is unavailable. Never request secrets in chat.

## GitHub control status

CI workflow and gate are implemented in this branch; no remote CI result has been confirmed yet. Branch protection status is unverified; native auto-merge was disabled in the last available repository metadata. Available tooling cannot configure these settings; exact administrator steps are in the application README. Never bypass repository rules.
