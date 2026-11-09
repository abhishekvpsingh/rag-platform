# Retrieval and answers

## Request flow

1. Authenticate, resolve tenant/user and verified source identities, and determine accessible collections.
2. Interpret topic, explicit dates, scope, and whether calculation or multi-hop work is needed.
3. Search keyword and vector candidates with tenant/access constraints. Use exact identifiers and metadata filters when useful.
4. Fuse results, deduplicate evidence, rerank a bounded candidate set, and resolve temporal applicability and authority.
5. Expand bounded parent context and reauthorize every evidence item before sending it to a model.
6. Generate a concise answer with claim-linked citations; validate citations, support, and numerical provenance.
7. Return answer status, evidence, coverage/freshness notes, and authorized historical suggestions.

## Techniques and budgets

Start with BM25 plus vector retrieval and reciprocal rank fusion. Add reranking after measuring its benefit. Query expansion and decomposition are selective, with explicit maximum subqueries, candidates, model calls, tokens, and time. Multi-hop and graph queries must follow the same access boundary.

Avoid routing that makes relevant authorized collections invisible. Evaluate recall when introducing tenant/collection partitioning. Retrieval similarity is not answer confidence or source authority.

## Evidence and citations

Citations contain source title, stable source URL, revision, and page/section/sheet locator plus a supporting span. Source URLs must be validated provider URLs, not arbitrary model-generated URLs. A valid citation ID alone does not prove a claim is supported; evaluate claim-to-evidence entailment and qualifications.

Treat retrieved text as untrusted data. Source instructions cannot alter system rules, trigger tools, or expand permissions. Keep retrieval and generation tools allowlisted.

## Answer behavior

Support statuses: answered, partial, conflicting, insufficient-evidence, and failed. Say what is unknown. Distinguish evidence from inference. Ask for location or employment scope when necessary to avoid a materially wrong policy answer. Historical suggestions must use accessible evidence and should not duplicate the main answer.

A user may see a partial corpus; explain incomplete indexing without revealing inaccessible titles or counts. Do not promise corpus-wide completeness from top-k results.

## Caches and streaming

Cache keys include tenant, authorization scope/epoch, index generation, model/configuration, and temporal context. Reauthorize cached evidence. Stream progress and draft tokens only after authorization; identify incomplete output if validation fails. Persisted chat history and export endpoints must recheck current evidence access and redact revoked source content.

## Validation

Measure candidate recall, ranking, answer support, citation precision, temporal selection, abstention, latency, and cost. Never make unsupported model self-confidence a correctness score.
