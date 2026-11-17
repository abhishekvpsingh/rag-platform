"""Real PostgreSQL + isolated parsers + OpenSearch with synthetic fixture embeddings.

Run inside the configured Linux API container. Creates and removes only a unique
database, temporary artifact directory and uniquely named tenant search index.
"""

import os
import secrets
import ssl
import tempfile
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
from alembic import command
from alembic.config import Config
from rag_api.identity.crypto import CredentialCipher
from rag_api.identity.service import IdentityService, database_engine, now
from rag_api.ingestion.artifacts import LocalArtifacts
from rag_api.ingestion.embeddings import FixtureEmbeddings
from rag_api.ingestion.models import Revision
from rag_api.ingestion.search import OpenSearchIndex
from rag_api.ingestion.service import IngestionService, run_pipeline
from rag_api.jobs.models import Job, WorkTarget
from sqlalchemy import select
from sqlalchemy.orm import Session


def main() -> None:
    base = os.environ["RAG_DATABASE_URL"]
    name = "ingestion_test_" + uuid4().hex
    url = base.rsplit("/", 1)[0] + "/" + name
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(name)))
    engine = database_engine(url)
    indexes: set[str] = set()
    client = httpx.Client(
        base_url=os.environ["RAG_SEARCH_URL"],
        auth=(os.environ["RAG_SEARCH_USERNAME"], os.environ["RAG_SEARCH_PASSWORD"]),
        verify=ssl.create_default_context(cafile=os.environ.get("RAG_SEARCH_CA")),
        timeout=15,
        trust_env=False,
        follow_redirects=False,
    )
    try:
        os.environ["RAG_DATABASE_URL"] = url
        command.upgrade(Config("alembic.ini"), "head")
        command.check(Config("alembic.ini"))
        identity = IdentityService(
            engine, CredentialCipher({"test": secrets.token_bytes(32)}, "test")
        )
        password = secrets.token_urlsafe(32)
        identity.bootstrap("fixture@example.test", password)
        token = identity.login("fixture@example.test", password).token
        connection = identity.add_connection(token, "google_drive", secrets.token_urlsafe(24))
        identity.verify_source_identity(
            token, connection, "synthetic-only", now() + timedelta(hours=1)
        )
        with tempfile.TemporaryDirectory() as directory:
            ingestion = IngestionService(identity, LocalArtifacts(Path(directory)))
            model = FixtureEmbeddings()
            for path in sorted(Path("tests/fixtures/ingestion").glob("policy.*")):
                job = ingestion.submit(
                    token,
                    connection,
                    path.name,
                    "fixture-v1",
                    path.suffix[1:],
                    path.read_bytes(),
                    model.config,
                )
                lease = ingestion.jobs.claim(job.tenant_id, job.id)
                assert lease
                run_pipeline(engine, lease, ingestion.artifacts, model, OpenSearchIndex(client))
                with Session(engine) as db:
                    completed = db.get(Job, (job.tenant_id, job.id))
                    assert completed and completed.state == "succeeded", path.suffix
                    revision = db.scalar(select(Revision).where(Revision.job_id == job.id))
                    assert revision and revision.index_name and revision.chunk_count
                    indexes.add(revision.index_name)
                    result = client.post(
                        "/" + revision.index_name + "/_search",
                        json={
                            "query": {
                                "bool": {
                                    "filter": [
                                        {"term": {"tenant": job.tenant_id}},
                                        {"term": {"revision": revision.id}},
                                        {"term": {"generation": revision.generation}},
                                    ]
                                }
                            },
                            "size": 100,
                        },
                    )
                    result.raise_for_status()
                    hits = result.json()["hits"]["hits"]
                    assert len(hits) == revision.chunk_count
                    assert all(h["_source"]["locator"] for h in hits)
                    assert all(len(h["_source"]["vector"]) == model.config.dimensions for h in hits)
                    target = db.get(WorkTarget, (job.tenant_id, job.target_id))
                    assert target and target.active_generation == revision.generation
                assert (
                    ingestion.submit(
                        token,
                        connection,
                        path.name,
                        "fixture-v1",
                        path.suffix[1:],
                        path.read_bytes(),
                        model.config,
                    ).id
                    == job.id
                )
        print("Seven synthetic formats parsed in isolation and indexed in real OpenSearch")
        print("Exact locators, dimensions, active generations and unchanged reuse passed")
    finally:
        os.environ["RAG_DATABASE_URL"] = base
        for index in indexes:
            response = client.delete("/" + index)
            response.raise_for_status()
        client.close()
        engine.dispose()
        with psycopg.connect(base, autocommit=True) as admin:
            admin.execute(
                psycopg.sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    psycopg.sql.Identifier(name)
                )
            )


if __name__ == "__main__":
    main()
