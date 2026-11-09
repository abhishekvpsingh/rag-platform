# Optional knowledge graph

## Product contract

Graph capability belongs in the final product and is disabled by default. An administrator can activate it in settings or accept a recommendation. Graph retrieval supplements hybrid search; ordinary questions do not require traversing a graph.

## When to recommend

Periodically assess privacy-preserving query categories, multi-document/multi-hop demand, repeated relationship failures, and evaluated retrieval gaps over a configurable lookback. Large files alone are not evidence of benefit. Require a minimum sample and distinguish model/parser failures from graph-relevant failures.

A recommendation includes observed evidence, limitations, estimated extraction/storage cost, affected corpus, and a bounded trial. Activation is explicit. Do not claim improvement without comparing graph-assisted and baseline retrieval on representative authorized questions.

## Data design

Entities and relationships retain tenant, source revision, evidence span, confidence, effective interval where relevant, and extractor version. Distinguish extracted assertions from reviewed facts. Contradictory relationships may coexist with provenance. Entity resolution must avoid joining unrelated people or organizations.

Graph node existence, labels, edges, aggregates, and paths can leak restricted information. Authorize evidence for every traversed assertion; derived paths are visible only when their supporting evidence is permitted. Cross-tenant entity merging is forbidden.

## Lifecycle

Disabled → estimating → trial/building → validating → active → paused/disabled. Initial build is resumable, budget-limited, and resource-isolated. Display coverage and freshness; partial graphs are not complete representations. Handle updated/deleted evidence incrementally. Disable graph querying immediately on deactivation; retention/purge follows tenant policy.

## Backend decision

Define GraphBackend contracts early. In the graph milestone, benchmark a supported backend and document operational and licensing tradeoffs in a decision record. Do not deploy an unused graph database in the initial Compose installation.

## Acceptance

Demonstrate quality improvement on selected relationship tasks, no regression for ordinary retrieval, access-safe traversal, deletion propagation, extraction-budget enforcement, fallback when the graph is unavailable, and deactivation without breaking hybrid answers.
