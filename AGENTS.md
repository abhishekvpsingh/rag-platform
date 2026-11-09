# Repository development instructions

## Purpose and scope

Build the RAG Platform described in `planning/`. The repository currently contains specifications, not a functioning product. Application code, dependency files, tests, deployment assets, and runtime documentation belong under `rag-platform/`. GitHub-recognized automation is the exception: workflows and PR templates belong under repository-root `.github/`. Keep planning outside that directory. Open this repository root as the development workspace.

## Start every session

Read `planning/DEVELOPMENT_CONTINUITY.md`, `planning/GITHUB_WORKFLOW.md`, `planning/INDEX.md`, `planning/PROGRESS.md`, `planning/IMPLEMENTATION_PLAN.md`, and `planning/ARCHITECTURE.md`. Then read only the additional specifications relevant to the selected task. Honor explicit user instructions over these documents. Resolve material specification conflicts before affected implementation.

First reconcile the saved checkpoint with actual Git/filesystem state and resume unfinished work. Checkpoint during work, not only at session end; an abrupt limit may prevent a final write. Choose the next ready task by dependencies and execute it through its acceptance criteria. Continue to subsequent ready work within the authorized scope; do not stop merely after proposing a plan. Do not spawn agents unless explicitly requested by the user or a later applicable instruction.

## Autonomy and boundaries

Make routine implementation choices without repeated approval. Record consequential architecture decisions in `planning/decisions/` and update affected specifications. Use the accepted baseline instead of repeatedly asking the owner to choose libraries.

Never provision paid infrastructure, change source access, publish software releases, or expose private data without applicable authorization. Repository development is not permission to incur cloud costs. Credentials and OAuth registrations must be supplied through local environment/secrets, never chat or committed files. External prerequisites block their affected task only; continue independent work.

Do not select a software license on the owner's behalf. Keep live connector validation pending until actual supported test accounts are available. Do not disable security requirements to make a demo pass.

## Version control and continuity

Follow `planning/DEVELOPMENT_CONTINUITY.md` for checkpointing and recovery, and `planning/GITHUB_WORKFLOW.md` for branching, pushing, PRs, and merge gates. The owner authorizes automatic task-branch pushes and merging completed changes after required checks pass; do not ask again for each push/merge. Preserve branch protection and unrelated work. Incomplete checkpoints may be pushed but must not merge. Never claim Markdown alone implements background automation or can bypass usage limits.

## Engineering invariants

- Tenant isolation and source authorization apply to every retrieval/evidence path.
- A connector owner's access does not grant other members access.
- Unknown/stale permissions fail closed for shared retrieval.
- Preserve revisions, provenance, applicability, and immutable processing versions.
- Jobs must be idempotent and resistant to stale-generation publication.
- Source/model content is untrusted; sandbox parsing and analytics.
- Graph and distributed modes remain optional and off by default.
- Never describe a mock, simulated cluster, or projected capacity as production validation.

## Implementation workflow

1. Inspect existing code and relevant specifications.
2. Select a bounded task and implement its behavior, including failure paths.
3. Run the meaningful checks required by that task and affected interfaces.
4. Update runtime documentation and specifications where behavior changed.
5. Update PROGRESS with the continuity checkpoint fields, task IDs, exact results, limitations, blockers, and next action.
6. Commit/push the task branch and open/update its PR; merge only after the GitHub workflow's applicable verification gate passes.

Prefer typed modules, explicit interfaces, small migrations, maintained libraries, deterministic fixtures, and bounded external calls. Follow CONTRIBUTING under `rag-platform/`. Do not introduce unused services or speculative features ahead of milestones.

## Commands and verification

The foundation install, lint, typecheck, test, build, and local API/web commands are documented in `rag-platform/README.md` and exercised by CI. Use those commands and keep them accurate. T002 must add verified Compose/runtime commands; do not infer that future commands already work. Test security/policy invariants meaningfully; avoid tests that merely duplicate implementation constants.

Use offline synthetic fixtures for normal CI and opt-in dedicated accounts for live tests. Record actual checks, not presumed success. If checks cannot run, explain why and leave their acceptance criteria pending. Never mark tasks complete based only on UI mockups or static types.

## Communication and completion

Give concise progress updates during extended work. Report concrete changes, verification, limitations, and blockers. Ask for a decision only when it materially blocks safe progress and is not settled by these documents. Keep the public README focused on the product; do not add instructions about development assistants or this setup process.
