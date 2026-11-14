# Security and permissions

## Trust boundaries

Browser, application identity, source identity, provider credentials, parser processes, model providers, search stores, artifact stores, and optional graph stores are distinct boundaries. Document content and model outputs are untrusted. A provider token is a service capability, not proof of an end user's entitlement.

## Authentication and roles

Use maintained authentication libraries, secure HttpOnly cookies, CSRF protection for cookie-authenticated mutations, explicit CORS, session expiry, and rate limits. Initial owner bootstrap must be one-time, local or token-protected, and disabled after completion. Add OIDC/SSO in the enterprise milestone; do not implement custom password cryptography.

Tenant context comes from authenticated membership, never an unchecked request field. Administrator configuration privileges do not grant source-document access. Use least-privilege service accounts and separate production secrets.

## Authorization pipeline

Enforce tenant/access restrictions before retrieval where supported, then reauthorize candidates before reranking, model transmission, previews, downloads, citations, graph traversal, and cached responses. Post-filtering alone is not sufficient isolation. Provider permission semantics and identity/group membership must be supported explicitly.

Initial owner-only connection content is private to that verified identity. Unknown ACLs or stale membership fail closed for shared access. Make authorization staleness configurable with a conservative default and explicit live-check fallback. Revoke query eligibility immediately when a revocation is observed; full source-change detection latency must be measured and disclosed.

Avoid unauthorized snippets, titles, counts, historical suggestions, graph entities, and timing-based existence signals where practical. Purge or redact persisted answer evidence when authorization changes; recheck stored histories on read.

## Content and execution safety

Sandbox parsers and analytics, bound extraction resources, reject dangerous file types, sanitize HTML, escape rendered model output, and validate source links. Prevent SSRF on download/preview paths using provider-host allowlists, redirect validation, and private-address protections. Never execute instructions inside retrieved documents.

## Secrets and external models

Encrypt refresh tokens using a deployment-managed key, support rotation, and exclude keys/tokens from logs and backups without encryption. Keep provider secrets server-side. Before external model use, disclose data transmission and enforce tenant provider/region policies. Local mode must not silently fall back to external APIs.

## Audit and privacy

Record configuration changes, connections, authorization decisions, administrative actions, migrations, and graph enablement with bounded metadata. Raw queries, responses, and file contents are excluded by default from operational logs. Diagnostic opt-in has retention and access controls. Aggregate recommendation telemetry locally by default.

## Release gates

Cross-tenant retrieval tests; connector-owner versus member tests; revoked groups and stale ACLs; citation/preview/history access; prompt injection; XSS; SSRF; malicious files; analytics escape attempts; secret scanning; dependency scanning; backup restoration with tombstone replay. Document remaining limitations and external security review status.

## T004 implementation boundary

See [identity runtime setup](../rag-platform/infra/IDENTITY.md) and
[ADR 0004](decisions/0004-identity-foundation.md) for the implemented owner-only
identity boundary, HTTPS configuration, local bootstrap, credential key rotation
primitive, current rate-limit scope and recovery checks. Shared source access and
provider-backed proof are not implemented by this foundation.
