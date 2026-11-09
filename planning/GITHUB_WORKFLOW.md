# GitHub and version-control workflow

## Standing authorization

The repository owner authorizes development sessions to create task feature branches, commit and push relevant code/checkpoints, open and update pull requests, and merge completed changes to main after the checks below pass. Do not ask for approval again for each authorized push or merge. Honor GitHub branch rules, required reviews, and any newer owner instruction.

This authorization does not permit paid provisioning, software release publication, deployment, source-permission changes, history rewriting, or committing private data.

## Branch and commit policy

- Keep main usable. Do all new implementation and documentation work on a task branch.
- Use feature/T001-short-description, fix/Txxx-short-description, or docs/short-description; include the task ID when available.
- Before branching, inspect status, fetch origin, and start from current origin/main without overwriting local changes. Resume an existing task branch when one exists.
- Prefer one bounded task or coherent change per PR. Use meaningful commits, for example feat(T007): add structure-aware chunking.
- Use wip(T007): checkpoint parser recovery for explicitly incomplete checkpoints.
- Stage explicit task-owned paths after reviewing their diff. Never blindly stage secrets, datasets, generated indexes, or other sessions' changes.
- Push normal commits with upstream tracking. Never force-push or use destructive reset/clean as routine recovery.
- Checkpoints with failing/incomplete tests may be pushed to their feature branch and draft PR, with accurate status; they are never merge-ready.

## Normal development cycle

1. Read development checkpoint and task acceptance criteria.
2. Create or resume the task branch.
3. Implement a bounded step and checkpoint according to DEVELOPMENT_CONTINUITY.md.
4. Run applicable local checks and record results.
5. Review the staged diff for correctness, secrets, unrelated edits, and generated artifacts.
6. Commit and push the branch; confirm the remote head.
7. Create or update a PR against main with problem/result, task IDs, tests, and limitations. Draft until complete.
8. Wait for the required CI checks and reviews on the latest pushed head. Fix failures on the same branch and rerun.
9. Merge only when the merge gate below passes.
10. Fetch and verify the merge, reconcile PROGRESS.md without fabricating checks, and start the next ready task from updated main.

If credentials/network access fail, preserve local commits and checkpoint the blocked push. Do not request tokens in chat or claim remote work happened. GitHub CLI is a convenient implementation path when available; equivalent authorized GitHub tools are acceptable.

## Merge gate

All conditions must hold:

- The scoped task/change acceptance criteria are satisfied; unfinished milestone work is not falsely marked complete.
- Applicable lint, type checks, tests, builds, security/permission checks, and evaluations pass.
- Required GitHub checks are successful for the current PR head and required branch rules/reviews are satisfied.
- Required live integration criteria are not replaced with mocks. A blocked live test keeps the affected task incomplete; independent verified foundation work may merge if its scope is explicit.
- The diff contains only intended changes and no credentials, private data, accidental outputs, or unreviewed dependency changes.
- Progress/specifications/runtime instructions match actual behavior and verification.
- The branch is compatible with current main. Integrate changed main through a normal merge when necessary, resolve conflicts, push, and rerun affected checks.
- Use an expected PR head SHA when merging so new untested commits cannot slip into the merge.

Failed, pending, missing, cancelled, or skipped required checks are not passing checks. Never bypass branch protection or weaken tests to merge. A successful check from an older commit is not evidence for the current head.

Prefer squash merge for completed task PRs, retaining useful task context in the PR description. Do not delete a branch/worktree containing unique unfinished work. Branch deletion after verified merge is optional.

## CI and GitHub setup

Markdown describes the policy; it does not execute pushes, enforce protection, or restart paused sessions. T001 must implement and verify the executable automation:

- GitHub Actions workflows under repository-root .github/workflows/ (GitHub requires this location), targeting code under rag-platform/.
- Triggers on pull_request to main and pushes to task branches; add main push validation. Avoid broad path filters that leave required checks permanently pending.
- Stable required check names for backend/frontend checks, integration tests when needed, and a final CI gate that fails on failed/cancelled/unexpectedly skipped prerequisites.
- Documentation-only changes can use applicable link/fence and policy checks; the final gate must explicitly validate legitimate skips of code checks.
- Least-privilege workflow permissions, pinned/reviewed action versions, no production secrets for ordinary PR CI, no unsafe execution of untrusted PR code with elevated tokens.
- Serialize overlapping runs per branch as appropriate and ensure cancellation cannot count as successful verification.
- Configure a main ruleset/branch protection requiring a PR and the final CI gate, plus an up-to-date branch or supported merge queue. Apply through authorized tooling if available; otherwise record the exact remaining repository-admin setting.
- Enable native auto-merge when supported, then arm it only after local criteria are satisfied. If unavailable, the active development session may merge through GitHub after verifying the same gate.
- If required human reviews are configured, wait for them; standing authorization is not a review bypass.

No unattended merge service is established by this document. If the session stops while CI runs, native GitHub auto-merge can finish only if configured and armed; otherwise the next session checks status and merges. Preserve that distinction in the checkpoint.

## Bootstrap exception for documentation

Before executable CI exists, documentation-only PRs may merge after explicit local link/fence/content validation and diff review, provided no configured repository rule requires additional checks. Record that there is no CI, rather than claiming it passed. This exception never applies to application code, dependencies, executable scripts, or workflow changes. Once CI exists, documentation changes use its documentation checks.

## Default recovery commands

Use these read-only checks when resuming, adapting branch names to observed state:

```bash
git status --short --branch
git remote -v
git log -5 --oneline
git worktree list
git fetch origin
```

Inspect output before switching branches. Do not interpolate secret values into commands or logs. Use structured tool arguments or a temporary body file for multiline PR descriptions.
