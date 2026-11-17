"""Owner-authorized revisions, idempotent processing and atomic generation activation."""

import hashlib
import time
from collections.abc import Callable
from uuid import uuid4

from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rag_api.identity.models import Connection, Membership, SourceIdentity, User
from rag_api.identity.service import AccessDenied, IdentityService, utc
from rag_api.ingestion.artifacts import LocalArtifacts
from rag_api.ingestion.chunking import CHUNKER_VERSION, chunks
from rag_api.ingestion.embeddings import Embedder, EmbeddingConfig, ProviderFailure
from rag_api.ingestion.models import Document, Revision, SourceVersion
from rag_api.ingestion.parsing import PARSER_VERSION, Parsed, ParseFailure
from rag_api.ingestion.sandbox import isolated_parse
from rag_api.ingestion.search import OpenSearchIndex, SearchFailure
from rag_api.jobs.models import Job, WorkTarget
from rag_api.jobs.service import JobConflict, JobService, Lease


def processing(config: EmbeddingConfig) -> str:
    return hashlib.sha256(
        f"{PARSER_VERSION}/{CHUNKER_VERSION}/{config.fingerprint}/{config.max_input_bytes}".encode()
    ).hexdigest()


class IngestionService:
    def __init__(self, identity: IdentityService, artifacts: LocalArtifacts) -> None:
        self.identity, self.artifacts = identity, artifacts
        self.jobs = JobService(identity.engine)

    def submit(
        self,
        token: str,
        connection_id: str,
        source_key: str,
        source_version: str,
        format: str,
        content: bytes,
        config: EmbeddingConfig,
    ) -> Job:
        for attempt in range(2):
            try:
                return self._submit(
                    token, connection_id, source_key, source_version, format, content, config
                )
            except IntegrityError:
                if attempt:
                    raise JobConflict() from None
        raise JobConflict()

    def _submit(
        self,
        token: str,
        connection_id: str,
        source_key: str,
        source_version: str,
        format: str,
        content: bytes,
        config: EmbeddingConfig,
    ) -> Job:
        principal = self.identity.authorize_source(token, connection_id)
        if not 1 <= len(source_key) <= 512 or not 1 <= len(source_version) <= 256:
            raise ValueError("Invalid source identifiers")
        if format not in {"txt", "md", "html", "csv", "pdf", "docx", "xlsx"}:
            raise ParseFailure("unsupported_format")
        key = self.artifacts.put(principal.tenant_id, content)
        version = processing(config)
        with Session(self.identity.engine, expire_on_commit=False) as db, db.begin():
            IdentityService.resolve(db, token)
            # Target locks serialize updates; unique source IDs fence first creation.
            connection = db.scalar(
                select(Connection).where(
                    Connection.tenant_id == principal.tenant_id, Connection.id == connection_id
                )
            )
            if (
                connection is None
                or not connection.active
                or connection.owner_id != principal.user_id
            ):
                raise AccessDenied()
            target: WorkTarget | None
            document = db.scalar(
                select(Document).where(
                    Document.tenant_id == principal.tenant_id,
                    Document.connection_id == connection_id,
                    Document.source_key == source_key,
                )
            )
            if document is None:
                identifier = str(uuid4())
                target = WorkTarget(
                    tenant_id=principal.tenant_id,
                    id=identifier,
                    owner_id=principal.user_id,
                    generation=1,
                    tombstoned=False,
                )
                db.add(target)
                db.flush()
                document = Document(
                    tenant_id=principal.tenant_id,
                    id=identifier,
                    connection_id=connection_id,
                    source_key=source_key,
                )
                db.add(document)
                db.flush()
            else:
                target = db.scalar(
                    select(WorkTarget)
                    .where(
                        WorkTarget.tenant_id == principal.tenant_id, WorkTarget.id == document.id
                    )
                    .with_for_update()
                )
                assert target is not None
                if target.tombstoned:
                    raise JobConflict()
                prior = db.scalar(
                    select(Revision).where(
                        Revision.tenant_id == principal.tenant_id,
                        Revision.document_id == document.id,
                        Revision.generation == target.generation,
                    )
                )
                if (
                    prior
                    and prior.content_hash == key
                    and prior.processing_version == version
                    and prior.format == format
                ):
                    job = db.get(Job, (principal.tenant_id, prior.job_id))
                    assert job is not None
                    self.record_version(db, principal.tenant_id, document.id, source_version, key)
                    return job
                target.generation += 1
            self.record_version(db, principal.tenant_id, document.id, source_version, key)
            now = self.jobs.clock()
            job_id, revision_id = str(uuid4()), str(uuid4())
            job = Job(
                tenant_id=principal.tenant_id,
                id=job_id,
                owner_id=principal.user_id,
                target_id=document.id,
                generation=target.generation,
                kind="ingest",
                processing_version="ingestion-v1",
                idempotency_key=hashlib.sha256(revision_id.encode()).hexdigest(),
                state="queued",
                attempts=0,
                max_attempts=3,
                progress=0,
                duration_seconds=0,
                created_at=now,
                updated_at=now,
                available_at=now,
            )
            db.add(job)
            db.flush()
            db.add(
                Revision(
                    tenant_id=principal.tenant_id,
                    id=revision_id,
                    document_id=document.id,
                    job_id=job_id,
                    source_version=source_version,
                    content_hash=key,
                    format=format,
                    generation=target.generation,
                    processing_version=version,
                    embedding_model=config.model,
                    embedding_revision=config.revision,
                    dimensions=config.dimensions,
                    embedding_provider=config.provider,
                    parser_version=PARSER_VERSION,
                    chunker_version=CHUNKER_VERSION,
                    input_byte_limit=config.max_input_bytes,
                    observed_at=now,
                )
            )
            self.jobs.event(db, job, now)
            IdentityService.audit(db, principal, "ingestion.created")
            return job

    def record_version(
        self, db: Session, tenant: str, document: str, version: str, key: str
    ) -> None:
        existing = db.get(SourceVersion, (tenant, document, version))
        if existing:
            if existing.content_hash != key:
                raise JobConflict()
        else:
            db.add(
                SourceVersion(
                    tenant_id=tenant,
                    document_id=document,
                    source_version=version,
                    content_hash=key,
                    observed_at=self.jobs.clock(),
                )
            )


def authorized(db: Session, jobs: JobService, lease: Lease) -> tuple[Job, Revision, Document]:
    job = jobs.live_lease(db, lease)
    if job is None or jobs.invalidate_if_needed(db, job):
        raise AccessDenied()
    revision = db.scalar(
        select(Revision).where(
            Revision.tenant_id == lease.tenant_id, Revision.job_id == lease.job_id
        )
    )
    if revision is None:
        raise AccessDenied()
    document = db.get(Document, (lease.tenant_id, revision.document_id))
    assert document is not None
    connection = db.scalar(
        select(Connection)
        .where(Connection.tenant_id == lease.tenant_id, Connection.id == document.connection_id)
        .with_for_update()
    )
    # Lock authorization rows through activation, serializing concurrent revocation.
    source = db.scalar(
        select(SourceIdentity)
        .where(
            SourceIdentity.tenant_id == lease.tenant_id,
            SourceIdentity.connection_id == document.connection_id,
            SourceIdentity.user_id == job.owner_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    membership = db.scalar(
        select(Membership)
        .where(
            Membership.tenant_id == lease.tenant_id,
            Membership.user_id == job.owner_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    user = db.scalar(
        select(User)
        .where(User.id == job.owner_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        not membership
        or not membership.active
        or not user
        or not user.active
        or not connection
        or not connection.active
        or connection.owner_id != job.owner_id
        or not source
        or utc(source.verified_until) <= jobs.clock()
    ):
        raise AccessDenied()
    return job, revision, document


def run_pipeline(
    engine: Engine,
    lease: Lease,
    artifacts: LocalArtifacts,
    embedder: Embedder,
    search: OpenSearchIndex,
    parser: Callable[[bytes, str], Parsed] = isolated_parse,
) -> None:
    jobs = JobService(engine)

    def snapshot() -> tuple[Revision, Document]:
        with Session(engine, expire_on_commit=False) as db, db.begin():
            _, revision, document = authorized(db, jobs, lease)
            return revision, document

    started = time.monotonic()
    try:
        revision, document = snapshot()
        if processing(embedder.config) != revision.processing_version:
            raise ProviderFailure(False)
        parsed = parser(artifacts.read(lease.tenant_id, revision.content_hash), revision.format)
        passages = chunks(parsed, embedder.config.max_input_bytes)
        vectors: list[list[float]] = []
        for offset in range(0, len(passages), embedder.config.batch_size):
            if time.monotonic() - started > 240:
                raise ParseFailure("processing_time_limit")
            snapshot()  # Reauthorize before each external model transmission.
            if not jobs.heartbeat(lease, 10 + int(70 * offset / max(1, len(passages)))):
                return
            vectors.extend(
                embedder.embed(
                    [p.text for p in passages[offset : offset + embedder.config.batch_size]]
                )
            )
        snapshot()
        if not jobs.heartbeat(lease, 85):
            return

        def checkpoint() -> bool:
            snapshot()
            return jobs.heartbeat(lease, 90)

        index = search.stage(
            lease.tenant_id,
            document.id,
            revision.id,
            revision.generation,
            document.connection_id,
            embedder.config,
            passages,
            vectors,
            checkpoint,
        )
        snapshot()
        output = artifacts.put(lease.tenant_id, parsed.model_dump_json().encode())

        def publish(db: Session, job: Job) -> str:
            _, current, _ = authorized(db, jobs, lease)
            current.output_key, current.index_name, current.chunk_count = (
                output,
                index,
                len(passages),
            )
            return "revision:" + current.id

        jobs.complete(lease, publish)
    except AccessDenied:
        jobs.fail(lease, transient=False)
    except ProviderFailure as exc:
        jobs.fail(lease, transient=exc.transient)
    except SearchFailure:
        jobs.fail(lease, transient=True)
    except (ParseFailure, ValueError):
        jobs.fail(lease, transient=False)
