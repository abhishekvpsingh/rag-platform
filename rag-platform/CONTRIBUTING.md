# Contributing

This repository is currently specification-first. Read the [product scope](../planning/PRODUCT.md), [architecture](../planning/ARCHITECTURE.md), and [implementation plan](../planning/IMPLEMENTATION_PLAN.md) before changing behavior.

## Development conventions

- Application code and runtime assets belong under `rag-platform/`; planning belongs under `planning/`.
- Target Python 3.12 with `uv`, FastAPI, typed code, Ruff, and pytest. Target Node.js 22 LTS, TypeScript, Next.js, pnpm, ESLint, and Playwright. Confirm dependency compatibility and commit lockfiles in the foundation milestone.
- Use small, coherent changes with meaningful tests. Do not introduce abstractions for hypothetical providers without a current contract need.
- Keep tenant identity and authorization explicit at service boundaries. Never log secrets or document contents by default.
- Database schema changes require migrations and a documented recovery strategy. Never edit an applied migration to change existing deployments.
- Keep provider-facing behavior behind adapters and test contracts independently of live credentials.

## Pull requests

Explain the problem, resulting behavior, scope, and validation. Link task IDs where applicable. Update the relevant specification when public behavior changes. Record consequential architecture changes in a decision record.

Do not describe stubbed connectors, sample data, or synthetic benchmarks as production validation. Include limitations and untested provider/account combinations.

## Checks

The foundation milestone must establish exact install, lint, typecheck, test, and build commands in the application README and CI. Until then, do not invent passing commands. Use the [evaluation specification](../planning/TESTING_AND_EVALUATION.md) to select required checks.

## Licensing

License selection remains open before software release. Do not add third-party code or assets without recording their license and compatibility.
