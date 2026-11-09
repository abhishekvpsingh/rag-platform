# Product specification

## Goal

Build a self-hosted web platform that turns connected company files into access-controlled, current, evidence-backed answers. Installation should be approachable for a single user and extensible to company deployments. The product must make unsupported files, incomplete synchronization, uncertainty, and operational limits visible.

## Users and roles

- Owner: bootstrap administration and manage the deployment.
- Administrator: configure connectors, identity mappings, models, authority rules, retention, and capacity.
- Member: ask questions and inspect only authorized evidence.
- Reviewer: evaluate policy conflicts and suggested document relationships within explicitly granted scope.

Keep application roles separate from source access: being an application administrator does not automatically authorize reading every source document.

## Initial release boundary

Single-node Docker Compose; Google Drive My Drive and personal OneDrive through delegated OAuth; PDF with text, DOCX, TXT, Markdown, HTML, CSV, and XLSX baseline support; hybrid retrieval; citations; current-policy resolution; durable incremental ingestion; a polished web UI; model-provider configuration; and safe operational controls.

Account scope is a product default chosen to keep development unblocked, not confirmation of the owner's account type. Work/school OneDrive and Google shared drives are planned in M5. If the first real test account requires them earlier, move the relevant task forward without silently claiming support.

OCR, complex spreadsheet analytics, enterprise federation, knowledge graphs, and multi-node deployment arrive in explicit later milestones. Graph retrieval and distributed deployment remain off by default in the final product. Existing ingestion must remain usable when optional capabilities are disabled.

## Core journeys

1. Administrator bootstraps a deployment, chooses model providers, connects a source, selects folders, and sees estimated work and progress.
2. A member asks a question, receives a concise answer with exact evidence, and opens a permitted source preview.
3. A policy question resolves applicability as of today or a requested historical date; conflicts are disclosed and relevant older policies may be offered.
4. A source update, deletion, or access change propagates through artifacts, indexes, caches, and optional graph data.
5. An administrator inspects failures, retries work, adjusts settings, and reviews measured upgrade recommendations.

## Product invariants

No access through a connector credential is automatically transferred to another user. No unsupported claims of freshness, availability, or scale. Incomplete ingestion cannot be presented as complete knowledge. External transmission of content must follow configured provider policy. Optional recommendations never silently provision resources or enable graph processing.

## Release acceptance

Both initial connectors work with real supported accounts, authorization and deletion tests pass, end-to-end answers cite real evidence, the temporal fixture suite passes, restore is demonstrated, and a documented workload meets published targets. A mock-only demo is not a release.

## Non-goals

Training a foundation model, guaranteeing every answer, automatic cloud-account creation, unrestricted SQL execution, editing source files, arbitrary file execution, and billion-file certification without benchmarks.

## Open external decisions

Owner must supply OAuth application registrations and consent, choose a software license, and later choose a cloud provider for guided provisioning. These block the affected publication or live integration only; they do not block local foundation work.
