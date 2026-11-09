# Deployment and scaling

## Modes

1. Single machine: default Docker Compose, persistent volumes, bounded workers, external model APIs optional.
2. Local distributed test: kind/k3d with simulated nodes and resource limits; not production availability or real provisioning validation.
3. Existing Kubernetes cluster: production path with Helm/manifests, shared artifact storage, secrets, and dedicated worker pools.
4. Guided cloud provisioning: later infrastructure templates for one selected supported cloud account. Cloud credentials and administrator authorization are required.

Setup presents supported modes honestly. Until distributed implementation passes its milestone, show its roadmap status rather than a nonfunctional toggle.

## Two-level autoscaling

Application controllers scale worker instances from queue age/depth, query concurrency, latency, and resource signals. The infrastructure autoscaler adds machines when those instances cannot fit. Configure machine pool minimum/maximum, allowed instance classes, CPU/memory, worker requests/limits, cooldown, concurrency, and budgets.

A worker instance is not a machine and a CPU core is not a node. Keep worker capacity and machine capacity distinct in the UI. Infrastructure machine limits are enforceable; monetary estimates and alerts are not exact billing guarantees.

## Workload isolation

Separate query, ingestion CPU/OCR, and optional GPU pools. Scale source fetches only within provider quotas. Diagnose model throttling, bad queries, permission-filter overhead, disk pressure, and index issues before recommending more machines. Stateful search/database scaling needs storage, replicas, rebalancing, and recovery procedures, not aggressive job-style scale-down.

## Local testing

Target a lightweight development profile using external model APIs and configurable low worker limits. Record actual Mac RAM/CPU requirements after testing; do not promise the complete stack fits in 2–3 cores with arbitrary RAM. Simulated multiple nodes share one physical machine and cannot prove host failure resilience.

## Capacity advisor

Use configurable lookback windows, minimum samples, queue age, sustained utilization, query latency, data growth, and cost trends. Provide evidence, bottleneck diagnosis, expected benefit, prerequisites, and estimated cost. Recommendations do not enable distributed deployment, provision machines, or change the user's capacity ceilings automatically.

## Guided migration

Preflight target capacity/connectivity/secrets and compatible versions → backup → provision selected infrastructure → copy durable state/artifacts → restore/rebuild derived indexes → catch up changes → validate permissions, coverage, and queries → cut over → retain bounded rollback.

Use a maintenance window for the first migration implementation rather than pretending to offer zero downtime. Avoid dual writers; record migration ownership and checkpoints. A user can abort before cutover. Rollback must honor newly observed revocations and deletions.

## Production checks

Load balancer and TLS, readiness/liveness, graceful worker drain, disruption budgets, storage classes, backup destinations, resource quotas, restricted network policy, cluster-autoscaler integration, failure recovery, and measured SLOs. Never expose database/search/broker management ports publicly by default.
