# Synthetic evaluation workload v1

This corpus is invented public test content. `corpus.json` is shared by disjoint
`tuning.json` and `heldout.json` question IDs. Keep held-out questions out of
prompt/retriever tuning; version the dataset when changing them. No source accounts,
credentials, model downloads, or network calls are used.

Targets fixed before the first baseline run:

- Recall@3 >= 0.90 across cases with expected evidence.
- Zero forbidden evidence; zero unknown, duplicate, wrong-revision or invalid-locator citations.
- Warm in-memory p95 <= 50 ms per full held-out split, concurrency 1, 100 repetitions
  on the owner's Intel Mac (16 logical CPUs / 16 GiB RAM). Timing is opt-in, not a CI gate.

These targets apply to this tiny fixture harness, not product latency or capacity.
The reference baseline uses Unicode token overlap with synthetic tenant, explicit
reader/owner grants, permission freshness, deletion, parse state, region, and date
filters. Unknown/stale/revoked permissions fail closed. Connector ownership grants
no other actor access. The scorer independently checks raw adapter output; it does
not remove forbidden evidence before measuring leaks.

`travel.csv` supplies the immutable synthetic structured dataset; its declared
USD total is checked for fixture consistency, not treated as implemented analytics.

Expected evidence resolves to exact revisions/locators. Cases encode answer,
abstain, conflict, and analytical behaviors; analytical cases include numeric
answers. The runner measures retrieval and citation integrity only. It does not
generate answers or validate prompt injection resistance, SQL execution, provider
ACLs, or complete temporal policy rules. Injection and corrupt inputs are inert
fixture text/metadata. Those product gates arrive with their implementations.

Reports identify exact corpus/split/artifact bytes by SHA-256, processing/baseline versions,
and explicit `none` model/index/prompt versions. Normal output is deterministic;
`--benchmark` adds timings. Never report this reference baseline as product validation.
