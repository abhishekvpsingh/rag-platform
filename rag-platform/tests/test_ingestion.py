"""Synthetic fixtures test parser coordinates, isolation and publication boundaries."""

import io

# XML fixtures intentionally retain their canonical namespace URIs.
import platform
import subprocess
import sys
import zipfile
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from rag_api.identity.models import Connection
from rag_api.identity.service import AccessDenied, IdentityService, now
from rag_api.ingestion.artifacts import LocalArtifacts
from rag_api.ingestion.chunking import chunks
from rag_api.ingestion.embeddings import (
    CompatibleEmbeddings,
    EmbeddingConfig,
    FixtureEmbeddings,
    ProviderFailure,
)
from rag_api.ingestion.models import Revision, SourceVersion
from rag_api.ingestion.parsing import MAX_FILE, ParseFailure, parse
from rag_api.ingestion.sandbox import isolated_parse
from rag_api.ingestion.search import OpenSearchIndex
from rag_api.ingestion.service import IngestionService, run_pipeline
from rag_api.jobs.models import Job, WorkTarget
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_identity import owner


def zipped(files: dict[str, str]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text)
    return output.getvalue()


def corpus() -> dict[str, bytes]:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 10 200 Td (Leave policy) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    pdf = io.BytesIO()
    writer.write(pdf)
    return {
        "txt": b"Leave policy\nFive days",
        "md": b"# Leave\nFive days",
        "html": b"<h1>Leave</h1><script>secret()</script><p>Five days</p>",
        "csv": b"name,days\nLeave,5\n",
        "pdf": pdf.getvalue(),
        "docx": zipped(
            {
                "word/document.xml": '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Leave policy</w:t></w:r></w:p></w:body></w:document>'  # noqa: E501
            }
        ),
        "xlsx": zipped(
            {
                "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Leave" r:id="rId1"/></sheets></workbook>',  # noqa: E501
                "xl/_rels/workbook.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',  # noqa: E501
                "xl/worksheets/sheet1.xml": '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Days</t></is></c></row><row r="2"><c r="A2"><v>5</v></c></row></sheetData></worksheet>',  # noqa: E501
            }
        ),
    }


@pytest.mark.parametrize(
    "format,locator",
    [
        ("txt", "line:1"),
        ("md", "line:1"),
        ("html", "html-text:1"),
        ("csv", "row:1"),
        ("pdf", "page:1"),
        ("docx", "body:1/paragraph"),
        ("xlsx", "sheet:Leave/row:1"),
    ],
)
def test_formats_and_exact_locators(format: str, locator: str) -> None:
    parsed = parse(corpus()[format], format)
    assert parsed.blocks[0].locator == locator
    assert all("secret" not in b.text for b in parsed.blocks)
    if platform.system() == "Linux":
        assert isolated_parse(corpus()[format], format) == parsed


def test_unsafe_and_oversized_files() -> None:
    for data, format in [
        (b"x" * (MAX_FILE + 1), "txt"),
        (b"hello", "exe"),
        (b"not pdf", "pdf"),
        (b"a,b\nc", "csv"),
        (zipped({"../bad": "bad"}), "docx"),
        (zipped({"word/vbaProject.bin": "bad"}), "docx"),
        (
            zipped(
                {
                    "word/document.xml": '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>'
                }
            ),
            "docx",
        ),
    ]:
        with pytest.raises(ParseFailure):
            parse(data, format)


def test_unicode_chunks_are_bounded_reproducible_and_located() -> None:
    parsed = parse(("# Heading\n" + "界🙂 text " * 1000).encode(), "md")
    result = chunks(parsed, 256)
    assert result == chunks(parsed, 256)
    assert len(result) > 10
    assert all(len(x.text.encode()) <= 256 for x in result)
    assert result[-1].end == len(parsed.blocks[-1].text)
    assert all(x.section == "Heading" for x in result)
    assert len({x.id for x in result}) == len(result)


def test_artifact_isolation_integrity_and_symlinks(tmp_path: Path) -> None:
    store = LocalArtifacts(tmp_path)
    a, b = "a" * 36, "b" * 36
    key = store.put(a, b"document")
    assert store.put(a, b"document") == key
    with pytest.raises(FileNotFoundError):
        store.read(b, key)
    store.path(a, key).write_bytes(b"tampered")
    with pytest.raises(ValueError):
        store.read(a, key)
    with pytest.raises(ValueError):
        store.path("../private", key)


def test_provider_errors_order_and_dimension_validation() -> None:
    config = EmbeddingConfig("model", "rev1", 2)
    responses = [
        httpx.Response(429),
        httpx.Response(
            200,
            json={"data": [{"index": 1, "embedding": [3, 4]}, {"index": 0, "embedding": [1, 2]}]},
        ),
        httpx.Response(200, json={"data": [{"index": 0, "embedding": [1]}]}),
    ]
    client = httpx.Client(transport=httpx.MockTransport(lambda _: responses.pop(0)))
    model = CompatibleEmbeddings(
        config,
        "https://model.example/v1",
        "synthetic",
        frozenset({"https://model.example"}),
        client,
    )
    with pytest.raises(ProviderFailure) as error:
        model.embed(["test"])
    assert error.value.transient
    assert model.embed(["a", "b"]) == [[1, 2], [3, 4]]
    with pytest.raises(ProviderFailure) as error:
        model.embed(["test"])
    assert not error.value.transient


@pytest.mark.skipif(platform.system() != "Linux", reason="OS isolation runs in Linux/Compose")
def test_sandbox_denies_network_file_reads_and_exec() -> None:
    script = """from rag_api.ingestion.sandbox import restrict_linux
import socket, os
restrict_linux()
for action in (lambda: socket.socket(), lambda: open('/etc/passwd'), lambda: os.fork()):
    try:
        action()
    except PermissionError:
        continue
    raise SystemExit(1)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        timeout=10,
        env={"PYTHONPATH": str(Path(isolated_parse.__code__.co_filename).resolve().parents[2])},
    )
    assert completed.returncode == 0


def test_generation_pipeline_reuse_and_revocation(service: IdentityService, tmp_path: Path) -> None:
    token = owner(service)
    connection = service.add_connection(token, "google_drive", "fixture")
    service.verify_source_identity(token, connection, "subject", now() + timedelta(hours=1))
    ingestion = IngestionService(service, LocalArtifacts(tmp_path))
    model = FixtureEmbeddings()
    job = ingestion.submit(
        token, connection, "file-1", "v1", "md", b"# Leave\nFive days", model.config
    )
    assert (
        ingestion.submit(
            token, connection, "file-1", "v1", "md", b"# Leave\nFive days", model.config
        ).id
        == job.id
    )
    assert (
        ingestion.submit(
            token, connection, "file-1", "new-etag", "md", b"# Leave\nFive days", model.config
        ).id
        == job.id
    )
    with Session(service.engine) as db:
        assert db.get(SourceVersion, (job.tenant_id, job.target_id, "new-etag")) is not None
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"errors": False})

    client = httpx.Client(base_url="https://search.example", transport=httpx.MockTransport(respond))
    lease = ingestion.jobs.claim(job.tenant_id, job.id)
    assert lease is not None
    run_pipeline(service.engine, lease, ingestion.artifacts, model, OpenSearchIndex(client), parse)
    with Session(service.engine) as db:
        target = db.get(WorkTarget, (job.tenant_id, job.target_id))
        assert target and target.active_generation == 1
        revision = db.scalar(select(Revision).where(Revision.job_id == job.id))
        assert revision and revision.chunk_count == 2
    assert any(r.url.path == "/_bulk" for r in requests)
    newer = ingestion.submit(token, connection, "file-1", "v2", "md", b"New policy", model.config)
    lease = ingestion.jobs.claim(newer.tenant_id, newer.id)
    assert lease
    with Session(service.engine) as db, db.begin():
        conn = db.get(Connection, (job.tenant_id, connection))
        assert conn
        conn.active = False
    count = len(requests)
    run_pipeline(service.engine, lease, ingestion.artifacts, model, OpenSearchIndex(client), parse)
    assert len(requests) == count
    with Session(service.engine) as db:
        failed = db.get(Job, (job.tenant_id, newer.id))
        assert failed and failed.state == "failed"
    with pytest.raises(AccessDenied):
        ingestion.submit(token, connection, "file-1", "v3", "txt", b"no", model.config)


@pytest.mark.parametrize("invalidate", ["generation", "tombstone", "cancel"])
def test_inflight_output_cannot_activate(
    service: IdentityService, tmp_path: Path, invalidate: str
) -> None:
    token = owner(service)
    connection = service.add_connection(token, "google_drive", "fixture")
    service.verify_source_identity(token, connection, "subject", now() + timedelta(hours=1))
    ingestion = IngestionService(service, LocalArtifacts(tmp_path))
    model = FixtureEmbeddings()
    job = ingestion.submit(token, connection, "source", "v1", "txt", b"Old text", model.config)
    lease = ingestion.jobs.claim(job.tenant_id, job.id)
    assert lease

    def response(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/_bulk":
            if invalidate == "cancel":
                ingestion.jobs.cancel(token, job.id)
            else:
                ingestion.jobs.invalidate_target(token, job.id, invalidate == "tombstone")
        return httpx.Response(200, json={"errors": False})

    client = httpx.Client(
        base_url="https://search.example", transport=httpx.MockTransport(response)
    )
    run_pipeline(service.engine, lease, ingestion.artifacts, model, OpenSearchIndex(client), parse)
    with Session(service.engine) as db:
        target = db.get(WorkTarget, (job.tenant_id, job.target_id))
        assert target and target.active_generation is None
        revision = db.scalar(select(Revision).where(Revision.job_id == job.id))
        assert revision and revision.output_key is None


def test_provider_retry_and_owner_isolation(service: IdentityService, tmp_path: Path) -> None:
    from test_identity import member

    token = owner(service)
    connection = service.add_connection(token, "google_drive", "fixture")
    service.verify_source_identity(token, connection, "subject", now() + timedelta(hours=1))
    ingestion = IngestionService(service, LocalArtifacts(tmp_path))

    class Flaky(FixtureEmbeddings):
        calls = 0

        def embed(self, texts: list[str]) -> list[list[float]]:
            self.calls += 1
            if self.calls == 1:
                raise ProviderFailure(True)
            return super().embed(texts)

    model = Flaky()
    for other in (member(service, service.authenticate(token).tenant_id), member(service)):
        with pytest.raises(AccessDenied):
            ingestion.submit(other, connection, "file", "v1", "txt", b"private", model.config)
    job = ingestion.submit(token, connection, "file", "v1", "txt", b"private", model.config)
    client = httpx.Client(
        base_url="https://search.example",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"errors": False})),
    )
    lease = ingestion.jobs.claim(job.tenant_id, job.id)
    assert lease
    run_pipeline(service.engine, lease, ingestion.artifacts, model, OpenSearchIndex(client), parse)
    with Session(service.engine) as db, db.begin():
        retry = db.get(Job, (job.tenant_id, job.id))
        assert retry and retry.state == "retrying"
        retry.available_at = now() - timedelta(seconds=1)
    lease = ingestion.jobs.claim(job.tenant_id, job.id)
    assert lease
    run_pipeline(service.engine, lease, ingestion.artifacts, model, OpenSearchIndex(client), parse)
    with Session(service.engine) as db:
        complete = db.get(Job, (job.tenant_id, job.id))
        assert complete and complete.state == "succeeded" and complete.attempts == 2


def test_concurrent_revocation_prevents_publication(
    service: IdentityService, tmp_path: Path
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from rag_api.identity.models import SourceIdentity

    if service.engine.dialect.name != "postgresql":
        pytest.skip("Concurrent revocation locks are verified on PostgreSQL")
    token = owner(service)
    connection = service.add_connection(token, "google_drive", "fixture")
    service.verify_source_identity(token, connection, "subject", now() + timedelta(hours=1))
    ingestion = IngestionService(service, LocalArtifacts(tmp_path))
    model = FixtureEmbeddings()
    job = ingestion.submit(token, connection, "file", "v1", "txt", b"private", model.config)
    lease = ingestion.jobs.claim(job.tenant_id, job.id)
    assert lease
    reached = Event()
    client = httpx.Client(
        base_url="https://search.example",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"errors": False})),
    )

    def execute() -> None:
        reached.set()
        run_pipeline(
            service.engine, lease, ingestion.artifacts, model, OpenSearchIndex(client), parse
        )

    with ThreadPoolExecutor(max_workers=1) as pool:
        with Session(service.engine) as db, db.begin():
            source = db.get(SourceIdentity, (job.tenant_id, connection, job.owner_id))
            assert source
            source.verified_until = now() - timedelta(seconds=1)
            db.flush()  # Hold the revocation row lock while publication starts.
            future = pool.submit(execute)
            assert reached.wait(5)
        future.result(timeout=10)
    with Session(service.engine) as db:
        target = db.get(WorkTarget, (job.tenant_id, job.target_id))
        assert target and target.active_generation is None
        completed = db.get(Job, (job.tenant_id, job.id))
        assert completed and completed.state == "failed"
