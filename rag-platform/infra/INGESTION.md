# Parser and indexing pipeline

T007 provides an internal owner-authorized ingestion service and local operator
submission command. Drive/OneDrive discovery, OAuth and browser upload/onboarding
remain later tasks. A connector must establish a supported, verified source
identity before submission; this pipeline does not create or bypass source proof.

## Flow and storage

A submission stores a tenant-scoped immutable original artifact and commits a
document revision, generation and durable job/outbox together. An unchanged current
content hash, format and processing configuration reuse the same job. Changed
content/configuration creates a new generation while the prior allowed generation
remains active until successful completion. Tombstoned targets reject new work.

The ingestion queue handler parses in isolation, creates bounded passages,
reauthorizes before embedding batches and indexing, stages deterministic OpenSearch
records, then commits the result/active-generation pointer atomically. Partial
search writes remain inactive. Raw indexes are not a product retrieval API:
T011 must filter authoritative active generations and recheck source authorization.
Revocation overrides any previous active pointer.

Original artifacts are SHA-256 addressed within tenant directories; parsed output
retains source locators. Revisions record provider/model revision, dimensions,
parser/chunker versions, byte limits and a processing fingerprint. Model identity
includes the configured endpoint, preventing equal model names on different
providers from sharing an embedding space. Files are private local-volume data,
not encrypted application backups; protect/encrypt the host disk and backups.

## Supported subset and limits

| Input | Behavior |
|---|---|
| UTF-8 TXT/Markdown | Nonempty lines, line numbers; Markdown heading context |
| HTML | Text nodes with text-node ordinals; scripts/styles/embedded active elements omitted; no links fetched |
| Text PDF | Page locators; pypdf extraction; blank/image-only pages fail with OCR required |
| DOCX | Body paragraph/table-row locators, heading styles and repeated table headers |
| CSV | Header/schema summary and row locators; UTF-8 comma-separated rectangular data |
| XLSX | Sheet names, cell references and row locators; values and headers; formulas rejected |

No macros, embedded objects, OCR, encrypted PDF, formula evaluation or analytical
aggregation. Language is not inferred; unknown language remains unknown.
Unsupported/corrupt/oversized inputs fail rather than silently indexing filenames.

Limits: 8 MiB input, 32 MiB aggregate ZIP expansion, 2,000 archive members, 200:1
per-member compression ratio, 200 PDF pages, 10,000 blocks, 2 MiB extracted text,
20,000 chunks. Parsing has 8 CPU seconds, 512 MiB virtual memory, bounded output,
and a 15-second parent wall timeout. ZIP members are never extracted onto disk.

The default passage limit is 2,048 UTF-8 bytes with up to 64 characters overlap,
within one source block. Unicode character offsets locate each passage in its
parent block. Byte limits conservatively bound byte-based tokenization; they are
not measured token counts. Real model-specific tuning remains pending evaluation.

Production parser calls require Linux with libseccomp. The child loads trusted
libraries/codecs, removes inherited environment credentials and file descriptors,
then installs a default-deny syscall policy before reading untrusted input.
It cannot open files, create sockets, fork or exec. Mac development uses Docker;
native macOS parsing intentionally fails closed. Pure parser functions are for
synthetic unit tests and the sandbox child, not a fallback for production input.

## Configure and submit

Build the current images, run migrations, and enable the dispatcher:

```bash
docker compose build
docker compose exec api alembic upgrade head
docker compose --profile jobs up -d dispatcher worker
```

Set provider values through the private environment/.env before recreating the
worker. No provider is enabled by default.

- RAG_EMBEDDING_MODE=compatible
- RAG_EMBEDDING_ENDPOINT: approved HTTPS base URL ending in the provider API prefix
- RAG_EMBEDDING_ALLOWED_ORIGINS: comma-separated exact HTTPS origins
- RAG_EMBEDDING_MODEL, RAG_EMBEDDING_REVISION, RAG_EMBEDDING_DIMENSIONS
- RAG_EMBEDDING_KEY: server-side secret, never a command argument or committed value

External configuration explicitly authorizes transmitting eligible passage text
to that provider. Only deployment operators configure these endpoints; no user
request can supply one. Redirects and proxy-environment inheritance are disabled.
Provider revision/compatibility must be validated for the chosen deployment.
Batches are limited to 16 inputs by default, with bounded response size and time.
429/408/5xx and transport failures use durable bounded retries; invalid results
fail permanently. There is no automatic provider fallback.

RAG_EMBEDDING_MODE=fixture is opt-in synthetic testing only. Its SHA-based vectors
are not semantic embeddings and must never be presented as product search quality.

The local CLI requires identity configuration and an existing authenticated
session with a verified, current connection. It prompts privately for the token:

```bash
PYTHONPATH=services/api/src uv run --frozen python -m rag_api.ingestion.cli   /path/to/file.txt --connection CONNECTION_ID --source-key SOURCE_ID   --source-version REVISION --format txt
```

The CLI only submits; the Linux worker performs parsing. Jobs appear in Operations
as Document ingestion. Cancellation and bounded replay use the T006 job API.
No source credential or session token belongs in chat, shell arguments or Git.

## Verification and migrations

```bash
PYTHONPATH=services/api/src uv run --frozen python scripts/verify_identity.py
docker compose run --rm --no-deps api python scripts/verify_ingestion.py
```

The first command uses disposable PostgreSQL/RabbitMQ fixtures for permissions,
jobs, migration round-trip/drift and identity restore. Linux pytest also tests
isolated formats and forbidden syscalls. The second uses configured local services
but creates only a unique synthetic database/index and temporary artifact directory;
it removes those test resources afterward. No supported source account/model key
is used. CI runs real OpenSearch integration in the Linux Compose runtime.

Migration 0003 adds empty document/revision tables without backfill. Back up before
upgrading; downgrading drops this metadata. Artifact/index cleanup, retention,
full document restore drills and provider-backed quality evaluation remain later
work. Job attempts, source generations and tombstones must govern any replay;
physical index presence alone never establishes authorization or visibility.
