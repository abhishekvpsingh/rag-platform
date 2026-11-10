# RAG Platform application

The development foundation includes a runnable Next.js overview and FastAPI service, pinned dependency lockfiles, offline smoke tests, and CI. **Storage connectors, authentication, ingestion, retrieval, and answers are not implemented yet.** Do not connect private company data to this foundation or expose it publicly.

## Prerequisites

- Python **3.12.14** and uv **0.13.5**.
- Node.js **22.23.4** and pnpm **10.34.9**.
- Git; Chromium for browser tests (installed through Playwright below).

Version files and package engine constraints are committed. Use your preferred version manager to select the pinned versions. Python and Node workspaces share this directory; GitHub automation lives at repository-root `.github/`.

## Install

From the repository root:

```bash
cd rag-platform
uv sync --frozen
pnpm install --frozen-lockfile
```

Install uv/pnpm from their official distributions if needed. uv can manage the pinned Python runtime. Do not replace lockfiles just to bypass an installation failure; inspect the active tool versions first.

## Run locally

Start the API in one terminal from `rag-platform/`:

```bash
uv run --frozen uvicorn rag_api.main:app --app-dir services/api/src --host 127.0.0.1 --port 8000
```

Start the web application in another terminal from the same directory:

```bash
pnpm dev
```

Open `http://127.0.0.1:3000`. API docs are at `http://127.0.0.1:8000/docs`; liveness is `GET /health/live`; `GET /api/v1/capabilities` truthfully reports unavailable features. These are public, non-sensitive endpoints. Liveness does not imply dependency readiness. The overview does not call the API yet; no CORS exception is needed.

Stop either process with Ctrl+C. No database or content artifacts are created by this milestone. Compose, worker runtime, persistence, authorization, and OAuth setup are later tasks.

## Verification

Run from `rag-platform/`:

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest
python scripts/check_docs.py
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm --filter @rag-platform/web exec playwright install chromium
pnpm test:e2e
```

On a fresh Linux machine, browser system libraries may require `playwright install --with-deps chromium`; macOS uses the normal install command. End-to-end tests start the production build on loopback port 3100; run `pnpm build` first and keep that port free. Do not reuse unrelated local servers. Browser tests cover desktop/mobile layout, status disclosure, keyboard navigation, and local links.

For manual production-build smoke testing:

```bash
pnpm --filter @rag-platform/web start --port 3000
```

This is a local build check, not a hardened production deployment. Unit/API tests use synthetic data and need no model or storage credentials. GitHub Actions runs documentation, backend, frontend, and a final **CI Gate** on every relevant PR/push. Full integration/security/evaluation checks will be added with their features; current smoke tests do not certify a production RAG system.

## Offline evaluation baseline

Run from this directory, with no services or credentials:

```bash
PYTHONPATH=services/api/src uv run --frozen python -m rag_api.evaluation
PYTHONPATH=services/api/src uv run --frozen python -m rag_api.evaluation --split tuning
PYTHONPATH=services/api/src uv run --frozen python -m rag_api.evaluation --benchmark
```

The first command emits a deterministic JSON report and exits nonzero if the
fixture recall/citation/access gates fail. `--benchmark` adds 100 warm serial
full-split timings; timing is not a CI gate. The runner is a reference fixture
baseline, not implemented product retrieval, authorization, or answer generation.
See [workload and targets](tests/fixtures/evaluation/README.md).

## Layout

| Directory | Responsibility |
|---|---|
| `apps/web/` | Next.js development overview and frontend/browser tests |
| `services/api/` | FastAPI process metadata and capabilities |
| `services/workers/` | Reserved for durable processing workers |
| `packages/connectors/` | Reserved for connector contracts/adapters |
| `infra/` | Reserved for Compose and later Kubernetes |
| `tests/` | API tests and future synthetic integration fixtures |
| `scripts/` | Repository documentation validation |

Operational logs, `.env` files, generated builds, indexes, dependencies, and private datasets must stay out of Git. See the [product overview](../README.md), [roadmap](../planning/IMPLEMENTATION_PLAN.md), and [current checkpoint](../planning/PROGRESS.md).

## Repository merge controls

The CI workflow is committed, but repository settings require separate administration. Under GitHub Settings → Rules → Rulesets (or Branches), protect `main`: require a PR, require the status check **CI Gate**, require branches up to date or a supported merge queue, disallow force pushes/deletion, and configure reviews as desired. Under Settings → General → Pull Requests, enable auto-merge if desired. These settings have not been applied or verified by this implementation; the available connector cannot update repository rules. An active development session can merge only after the documented gate passes and repository rules permit it.
