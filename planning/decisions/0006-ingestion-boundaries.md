# 0006 — Isolated parsing and versioned index publication

Status: accepted for T007 implementation.

## Decision

Use pypdf (BSD-3-Clause) for text PDFs and defusedxml (PSF license) for bounded
DOCX/XLSX XML processing; Python's standard library handles UTF-8 text, Markdown,
CSV and HTML text extraction. Initial support excludes OCR, encrypted PDFs,
embedded objects/macros and formula-bearing workbooks. HTML is stored as text,
never executable markup. License selection for our own release remains open.

Production parser calls use a scrubbed-environment Linux child, CPU/address-space/
output limits, parent wall timeout and a default-deny libseccomp syscall filter
after trusted imports/codecs load. No sockets, filesystem opens, subprocesses or
exec are permitted during parsing. Mac development runs this in Docker; unsupported
native platforms fail closed. The trusted pure parser function is only for unit
fixtures and the sandbox child. This is not a sandbox for arbitrary installed plugins.

Chunks retain block locators, Unicode character offsets, parent hashes and section
labels. UTF-8 byte bounds conservatively bound byte-tokenized model inputs; endpoint
operators must select a compatible model and input budget. Tokenizer-specific
chunk-size tuning is deferred until a real model is configured and evaluated.

Persist immutable source revision metadata, content hashes, parser/chunker/model
versions and dimensions. Reuse an unchanged current generation's job. Tenant-scoped
artifact paths retain original and parsed files. OpenSearch stores deterministic
chunk IDs in tenant/model-specific indexes, with source/revision/generation metadata.
Index writes are staging; only the PostgreSQL active-generation pointer authorizes
visibility. Future T011 retrieval MUST filter by this pointer and reauthorize sources.
No raw index endpoint is exposed as product retrieval.

## Alternatives and consequences

A generic document framework would add substantial parser/dependency surface
before a measured need. Native macOS sandbox startup was not reliable in this
environment, so no native fallback is enabled. Linux filtering is tested explicitly.

OpenSearch cannot share a transaction with PostgreSQL. Therefore partial/stale
index entries may remain physically stored but are never active evidence through
the product boundary. Cleanup/retention is later operational work. A completed
generation commits its result and active pointer atomically; rejected, cancelled
or superseded attempts cannot activate it.

Fixture embeddings are explicitly non-semantic and opt-in, with their own model
fingerprint. External endpoints require explicit HTTPS origin approval and credentials;
there is no fallback. Provider failures are classified for bounded T006 retries.

Related: T007, INGESTION.md, SECURITY_AND_PERMISSIONS.md, DATA_MODEL.md.
