# Data model

## Identity and ownership

Use opaque internal IDs and explicit `tenant_id` on tenant-owned records. Enforce tenant scoping in repository methods, database constraints, and integration tests; use PostgreSQL row-level security as defense in depth where compatible. Foreign keys must not permit cross-tenant associations.

| Entity | Required semantics |
|---|---|
| Tenant, User, Membership | Tenant role, account status, bootstrap ownership |
| SourceIdentity, GroupMembership | Provider subject, verified mapping, group freshness |
| ConnectorConnection | Provider, account type, selected scope, encrypted credential reference, sync state |
| SourceDocument | Connection-scoped stable source ID, canonical URL, MIME type, deletion state |
| DocumentRevision | Immutable provider version or ETag, content hash, source timestamps, processing generation |
| PermissionSnapshot | Grants, inheritance, provider semantics, observed time, authorization epoch |
| Artifact | Storage key, hash, type, encryption/retention attributes, revision |
| Chunk | Revision, section path, page/sheet/row locators, text hash, parent linkage |
| IndexGeneration | Parser/chunker/model versions, embedding dimensions, status, activation time |
| PolicyAssertion | Topic, status, authority, scope, effective interval, confidence, evidence |
| SupersessionEdge | Replacing/replaced document, scope, evidence, reviewer and confidence |
| Job, JobAttempt, OutboxEvent | Idempotency key, stage, lease, attempts, errors, publish state |
| AnswerRun, Citation, Feedback | Query trace, configuration version, evidence spans, redacted diagnostics |
| EvaluationRun, Recommendation | Dataset/configuration versions, metrics, evidence, user decision |

## Temporal rules

Represent effective intervals as `[valid_from, valid_to)` with explicit timezone/date semantics. Unknown dates remain unknown. Distinguish source modification time, ingestion observation time, business applicability time, and system record history. Store extracted assertions with provenance; reviewed assertions must not be silently overwritten by lower-confidence extraction.

An overwrite of one source file creates a revision. A separate document replacing it creates a supersession relationship. Supersession can be partial and scoped; do not assume a single global policy chain.

## Storage and indexes

Use unique constraints on tenant/connection/source ID and revision identity. Persist parser, chunker, embedding, prompt, and configuration versions. Avoid unbounded chunk text or embedding arrays in operational job rows. Search entries carry tenant, document, revision, authorization references, temporal attributes, and generation.

Deduplication may reuse work inside authorized storage boundaries, but never merge document identities, leak cross-tenant existence, or discard differing ACLs. Citation records point to immutable evidence; viewing them always rechecks current authorization and retention.

## Lifecycle

Discovered → downloaded → parsed → embedded → indexed → searchable. Expose independent content and permission status. Deletion/revocation supersedes intermediate states. Purge removes derived data and caches; backup expiry follows documented retention. Restores must replay deletion records before serving queries.

## Migration requirements

Each schema change includes upgrade handling, backfill limits, index impact, and recovery guidance. Large data migrations run as resumable jobs. Index generation activation is atomic in metadata; readers never combine incompatible embedding spaces.
