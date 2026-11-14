# Project progress

## Current state

T001 is complete and merged through [PR #2](https://github.com/abhishekvpsingh/rag-platform/pull/2). Mac local setup is verified. T002 is merged through PR #3 as c898645; the owner reports resolving the scanner issue manually. Post-merge CI is being verified. T003 is complete and merged through PR #4. T004 is complete and merged via PR #5 as daaa925. T005 web shell is in progress. No storage connectors, ingestion, retrieval, or answers exist yet.

## Task status

| Task | Status | Evidence |
|---|---|---|
| T001 | Complete, merged | [Verification record](verification/T001.md), [PR #2](https://github.com/abhishekvpsingh/rag-platform/pull/2), merge `ada2f08` |
| T002 | Complete, merged via PR #3 | [Verification evidence](verification/T002.md); merge c898645 |
| T003 | Complete, merged via PR #4 | [Verification](verification/T003.md) |
| T004 | Complete, merged | [Verification](verification/T004.md); PR #5, daaa925 |
| T005 | Local acceptance passed; CI pending | [Verification](verification/T005.md) |
| T006–T025 | Not started | Specifications only |

## Development checkpoint

- Updated at: 2026-11-14T04:40:24.629761+00:00.
- Session state: in-progress; T005 local acceptance passed, publication/CI pending.
- Active task: T005 responsive web shell and navigation.
- Feature branch: feature/T005-web-shell; base main daaa925c045e962ef56e2a854a12b12840d9b9aa.
- Last verified merge: T004 [PR #5](https://github.com/abhishekvpsingh/rag-platform/pull/5), merged 2026-11-14T04:33:19Z as daaa925. Both final head CI gates and GitGuardian passed at 86c4266; all post-merge main CI checks passed too.
- Changed files: shell/layout/navigation, six route screens, shared state presentation, loading/error/404 boundaries, CSS tokens, component/browser tests and documentation. Only task-owned edits; screenshots stay ignored.
- Completed: real route navigation with active-page/skip/focus semantics; responsive mobile/desktop; honest unavailable states without fake controls/metrics; working route error retry.
- Checks: pnpm format:check, lint, typecheck, build passed; 4 component tests and 6 desktop/mobile browser tests passed. Every route and overflow assertion checked. Desktop/mobile Settings screenshots visually inspected. Docs and diff checks passed. See [T005 evidence](verification/T005.md).
- Running operations: none locally. Commit/push will start GitHub checks.
- Next action: commit/push T005, open PR, verify latest-head checks, merge with expected SHA. Next ready task after T005 is T006 durable work engine.
- Blockers: none.
- Limits: no login/settings forms, provider connections, retrieval or live telemetry; no full WCAG certification. Future data workflows require their own state/authorization checks.

## Historical T002 integration checkpoint

- Updated at: 2026-11-10T16:26:07Z.
- Session state: in-progress; normal main integration locally verified; T002 merge remains externally blocked and the published integration head needs its own CI.
- Active task: T002, runtime/contracts. Local Mac acceptance and Linux CI passed at 5c006eb; this integration head requires its own CI.
- Feature branch: feature/T002-runtime-contracts, original workspace. Base main after integration: b9c4bc3ae2cbed6700389e44e946063bf67260eb (initial base ada2f08).
- Last confirmed pushed implementation: 5c006eb9e74592617143d4078c5ee727c6890b38; PR #3 remains open/draft. T003 PR #4 is verified merged as b9c4bc3.
- Changed files: normal merge of main's T003 evaluation, fixtures, report, CI command and docs. Only PROGRESS conflicted; resolved by retaining both task records and updating actual statuses. Ignored .env and .data/tls remain private and unstaged.
- Completed steps: recovered/published final TLS DN and shutdown checks; fixed Linux web signal handling by launching Node directly; full runtime CI passed. Integrated the independently verified T003 baseline without rewriting history.
- Exact checks: 35 T002 backend tests, Ruff/format/mypy/docs passed on recovery. T002 Linux runs 42852558994 and 42853285414 passed Documentation, Backend, Frontend, Runtime Integration and CI Gate at 5c006eb. Mac four-store restart/recreation, dependency failure/recovery and authenticated/private-port assertions are recorded in [T002 evidence](verification/T002.md). Combined merge checks: frozen sync (48 packages), Ruff check/format (27 files), mypy (19 sources), pytest (56 passed), docs (39 files/0 errors), diff checks and byte-identical offline report comparison all passed. Frontend unchanged; normal CI runs it.
- Running operations: no local runtime containers for rag-platform-dev were running at inspection. No local stack restart was needed for T003. All combined local checks completed; inspect PR #3 for the integration head's CI state.
- Mac resource evidence: ~1.41 GiB six-container sample, 3.72% of one core in that sample with multi-core recovery bursts; Docker VM ~7.65 GiB. See T002 evidence for per-service measurements and limitations.
- Blocker: GitGuardian incident 39882436 still flags the historical df9d5a5 synthetic test credential. No real service used it; fixture remediation is committed. Dashboard sign-in/classification as Test credential is needed; connector/CLI cannot perform it. Scanning/check enforcement is unchanged; no override, suppression or history rewrite.
- Next action: inspect the latest PR #3 integration-head checks and remote SHA. Merge only after classification plus every current-head gate/review passes. If external access remains unavailable, next independent ready task is T005 (T004 depends on T002).
- Risks/limitations: development runtime and fixture reference only; no product authentication, source authorization, connectors, ingestion, answers or durable application jobs. Source accounts/model credentials and owner licensing decisions still gate their future tasks/releases.

## T003 completion checkpoint

- Updated at: 2026-11-10T16:19:51Z.
- Session state: in-progress; completed; final-head Actions and GitGuardian passed; PR #4 squash merged.
- Active task: T003, offline evaluation baseline. acceptance complete and merged.
- Feature branch: feature/T003-evaluation-baseline; worktree /private/tmp/rag-platform-t003.
- Base main SHA: ada2f08a77377bc1968df942a64c37a47f941486. T003 depends only on T001 and imports no unmerged T002 code.
- Last confirmed pushed/locally verified implementation: 98da15b3204b2a0b9d6795296eb84ee11f01c781; origin/feature/T003-evaluation-baseline matches. Final tested head was 3e10963; all latest-head checks passed before expected-head squash merge.
- Remote PR: [T003 PR #4](https://github.com/abhishekvpsingh/rag-platform/pull/4), merged as b9c4bc3ae2cbed6700389e44e946063bf67260eb from head 3e10963b4d2c85126abbc02421cd48659e4b733d; T002 remains [PR #3](https://github.com/abhishekvpsingh/rag-platform/pull/3), draft and unmerged.
- Changed files: evaluation module/tests, versioned fixtures/CSV, reference report, CI offline runner command, runtime README, testing specification, decision 0001, verification record, this checkpoint. No unrelated work or dependency/lockfile changes.
- Completed steps: strict schema; deterministic Unicode lexical reference baseline; independent raw-output scorer; explicit grants/dates/revisions/locators/forbidden sources; disjoint tuning/held-out cases; artifact/runner hashes; documented quality/latency targets before first run. Full scope/limits in [verification](verification/T003.md).
- Exact checks: frozen install; Ruff check/format (14 files); mypy (6 sources); pytest (24 passed). Both CLI splits exit 0, Recall@3 1.0, zero forbidden/invalid citations. Two separate held-out processes compare byte-identically. Warm 100-run full-split p50 5.69 ms / p95 5.97 ms, target <=50 ms on declared Mac. Final docs: 38 Markdown files, zero link/fence errors; git diff --check passed. Final-head Documentation, Backend, Frontend, CI Gate and GitGuardian passed on PR #4.
- Running operations: T003 local commands completed; no service needed. T002 Actions run 42852558994 passed Backend, Frontend, Documentation, Runtime Integration and CI Gate for 5c006eb (direct Node shutdown fix); the duplicate PR-triggered run also passed. Existing T002 containers/previews not modified by T003.
- T002 recovery: final saved changes pushed as b936723; its new Linux stop-exit assertion failed. Follow-up 5c006eb runs web Node directly rather than through pnpm and reports per-service exit codes. The correction passed full Linux runtime CI in run 42852558994. No failed check was ignored. Original GitGuardian test-credential finding still requires dashboard classification.
- Blockers: no T003 blocker. T002 classification requires the separate GitGuardian dashboard; independent development continues.
- Next action: T003 is complete; reuse the versioned fixtures in later tasks. T002 is being integrated with this verified main.
- Risks/limitations: fixture reference results do not validate product retrieval, live ACLs, answer generation, temporal resolution, injection defense, analytics, or production performance. Owner license choice remains pending before release.

## External prerequisites and limitations

OAuth apps/test accounts and model credentials are required for later live tests. License/private reporting decisions precede a software release. Cloud choice/account/budget precedes T024. None blocks foundation development.

Main has no classic protection and no rulesets (verified 2026-11-10); native auto-merge was disabled in earlier metadata. Exact admin steps are in the application README. No repository controls were changed in this session.

Never ask for secrets in chat. Do not infer production readiness from foundation tests. Follow [continuity](DEVELOPMENT_CONTINUITY.md) and [GitHub workflow](GITHUB_WORKFLOW.md).
