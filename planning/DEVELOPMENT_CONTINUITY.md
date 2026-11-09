# Development continuity and recovery

## Purpose and limits

Resume unfinished development after context compaction, session expiration, a usage limit, an editor restart, or an abrupt interruption. Durable repository state is the handoff; chat history is supplementary.

This protocol cannot restart Codex automatically, bypass usage limits, or guarantee a final write after an abrupt cutoff. Once the user resumes or starts a session with repository access, recover from the latest checkpoint and actual Git/filesystem state. Frequent checkpoints limit lost context.

## Required reading on resume

Read root AGENTS.md, this document, GITHUB_WORKFLOW.md, PROGRESS.md, and the active task in IMPLEMENTATION_PLAN.md. Read the active task's specifications as needed. Resume unfinished work before selecting a new task unless blocked or redirected.

## Checkpoint policy

Update PROGRESS.md when starting a task, after a meaningful implementation step or check batch, before switching branches/tasks, and before an anticipated pause. During extended work, checkpoint at least every 15 minutes when execution permits; do not rely on being warned before limits.

Keep checkpoints concise and accurate. Save edited files to disk. Commit and push task-owned checkpoint changes on a feature branch after reviewing the diff for secrets and unrelated work. WIP checkpoints may have failing checks, but must be clearly marked, use a draft PR, and never merge until the merge gate passes. Include the checkpoint notes in the same commit when practical.

A pushed commit survives loss of the local workspace; an uncommitted file survives only if that workspace persists. Never claim remote preservation without confirming the push. If push fails, retain local work and record the failure.

## Checkpoint fields

Maintain these fields in PROGRESS.md; use pending/unknown rather than invented results:

- Updated at: UTC date/time.
- Session state: ready / in-progress / paused / blocked / ready-to-merge / completed.
- Active task ID and substep; acceptance criteria still open.
- Feature branch and base main SHA.
- Last verified implementation/checkpoint commit and confirmed remote branch/PR URL.
- Changed files and any intentionally uncommitted work.
- Completed steps and decisions, with links where useful.
- Exact checks: commands, outcome, tested commit or working-tree state, and relevant artifact locations.
- Running operations: command, durable job/run ID, output location, and whether completion was confirmed.
- Blockers: missing dependency/credential/decision and what work remains independent.
- Next action: concrete first command or implementation step.
- Risks/limitations and any merge eligibility restrictions.

Do not store secrets, private source data, raw customer prompts, ephemeral tokens, or sensitive logs in this public repository. Record a test command, not its secret-bearing environment values. Reference a commit by an existing SHA; do not try to embed a checkpoint commit's own SHA in itself.

## Resume procedure

1. Inspect repository root, remotes, current branch, git status, recent commits, and worktrees. Do not reset, clean, stash, overwrite, or discard unknown changes.
2. Fetch origin when authenticated and reachable. Compare the recorded branch/base/head against actual local and remote state. A missing checkpoint does not mean the work never happened.
3. Inspect uncommitted diffs and recent task commits. Determine whether they are task work, user work, another session's work, or uncertain. Preserve all unrelated work.
4. Locate the existing task branch and PR. Continue it rather than duplicating it. If already merged, verify merge status and criteria, update progress, and select the next task.
5. Reconcile stale checkpoint claims with code and test/CI evidence. A command that started but lacks a confirmed exit result is unverified. Do not repeat long-running or state-changing operations without checking their state.
6. Verify the environment and dependencies. Re-run checks affected by edits, environment changes, missing evidence, or an updated base; do not repeat expensive unaffected checks without reason.
7. Record the recovered state and next action, then continue the task. Resolve conflicts carefully and rerun affected checks; never force-push shared history.

## Concurrent sessions

Use one active writer per task branch and checkpoint. If another session appears active, avoid competing edits; use an isolated worktree/branch or ask only when ownership cannot be determined. Do not replace PROGRESS.md wholesale and erase another task's record.

## Before stopping

When possible, save work, update the checkpoint, review and commit task changes, push the feature branch, and leave a draft PR or update the existing PR. Summarize what is saved locally versus remotely and the exact next step. Keep incomplete work out of main.

## Recovery acceptance

T001 must establish a simple development continuity exercise: checkpoint an incomplete task, begin a fresh session, locate its branch/diff, distinguish unverified checks, and resume without duplicating or discarding work. An actual usage-limit event is not required to validate the protocol.
