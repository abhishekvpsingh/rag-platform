# Structured data

## Separation of responsibilities

Search locates and explains datasets. A controlled analytical engine computes totals, filters, joins, and aggregations. Embedding rows is not a substitute for accurate computation.

## Ingestion

For CSV/XLSX preserve source revision, sheet, header rows, inferred types, formulas versus cached values, units, encoding, delimiter, locale, and row locators. Flag uncertain type inference and missing/stale formula values. Never execute spreadsheet macros or fetch external formula references.

Initial support indexes bounded table summaries and headers with exact row provenance. Full analytics is a later milestone; until implemented, numerical aggregation requests must abstain or explain the limitation.

## Execution design

Use DuckDB in an isolated worker against immutable authorized snapshots. Allow read-only queries over explicitly registered datasets; deny arbitrary filesystem access, network access, extension installation/loading, external reads, and write statements. Parse/validate SQL and use process sandboxing; string-based keyword filtering is insufficient. Limit execution time, memory, scan bytes, rows, joins, and result size.

Only query datasets authorized for the requester. For row-level source restrictions, preserve equivalent enforcement or exclude the dataset from shared analytics. Do not assume file permission implies row-level filtering support.

## Answer provenance

Record dataset revision, sheet/range, validated query or structured plan, result, units, and execution time. Cite computed results separately from narrative document claims. Handle nulls, duplicates, currency, timezones, and precision explicitly. Do not silently combine incompatible datasets or stale snapshots.

## Acceptance

Fixtures include locale-specific numbers, misleading headers, missing values, duplicate rows, stale formulas, oversized sheets, malicious formulas, unauthorized joins, and exact expected aggregates. Resource-limit failures must terminate the worker and return a useful bounded error.
