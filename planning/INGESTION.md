# Ingestion pipeline

## Stages

Discover → authorize → download → validate → parse/OCR → normalize → version → chunk → enrich → embed → index → activate.

Each stage persists its input generation, output references, and status. Jobs use deterministic stage keys. Retry only transient failures; use capped attempts, jitter, dead-letter inspection, and administrative replay. A newer generation, tombstone, or revoked permission invalidates pending publication.

## File handling

Initial parsers cover text PDF, DOCX, TXT, Markdown, sanitized HTML, CSV, and XLSX. Extract headings, tables, page/sheet/row coordinates, language, and metadata. Never execute macros, scripts, links, or embedded objects. Apply file-size, expanded-size, page, row, CPU, memory, and time limits. Use isolated parser processes with restricted network access. Detect archive bombs and misleading MIME types.

OCR is an explicit later capability with language and page-confidence reporting. Encrypted, corrupt, oversized, unsupported, and partially parsed files receive visible status. Do not silently substitute filenames for content.

## Chunking

Default to structure-aware sections with token bounds and limited overlap. Preserve table headers and section hierarchy. Use child passages for retrieval and bounded parent context for generation. Record deterministic locators, parser/chunker version, and source revision. Tune chunk sizes on evaluation data rather than assuming one universal size.

## Efficiency

Content hashes avoid unchanged work while preserving source and permission identity. Reuse compatible embedding results within permitted boundaries. Batch provider calls with token and request limits. Respect source and model quotas. Small edits should avoid full reprocessing when stable structure supports it; correctness takes priority over fragile differential logic.

## Publication and reindexing

Publish a document generation only after its required chunks are available. Keep the previous allowed generation searchable during a content update, clearly exposing freshness; permission revocation overrides that behavior. Build incompatible model/index upgrades alongside the active generation, validate coverage and quality, then cut over atomically. Keep rollback only as long as authorization and retention permit.

## Visibility

Show discovered files, processed files, bytes/chunks, exclusions, errors, queue age, throughput, last successful sync, and coverage. Estimates must be labeled estimates; progress denominators can change during discovery. Ingestion never blocks interactive queries through unbounded shared resource consumption.
