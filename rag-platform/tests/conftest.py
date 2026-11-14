"""Synthetic shared runtime settings."""

import os
import secrets
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlunsplit

import pytest
from rag_api.identity.crypto import CredentialCipher
from rag_api.identity.models import Base
from rag_api.identity.service import IdentityService, database_engine
from sqlalchemy import event


@pytest.fixture
def runtime_env() -> dict[str, str]:
    def endpoint(scheme: str, host: str) -> str:
        credentials = "fixture:" + secrets.token_urlsafe(24)
        return urlunsplit((scheme, f"{credentials}@{host}", "/rag", "", ""))

    return {
        "RAG_DATABASE_URL": endpoint("postgresql", "postgres:5432"),
        "RAG_BROKER_URL": endpoint("amqp", "rabbitmq:5672"),
        "RAG_SEARCH_URL": "https://opensearch:9200",
        "RAG_SEARCH_USERNAME": "fixture-admin",
        "RAG_SEARCH_PASSWORD": secrets.token_urlsafe(24),
        "RAG_ARTIFACT_ROOT": "/var/lib/rag/artifacts",
    }


@pytest.fixture
def service(tmp_path: Path) -> Iterator[IdentityService]:
    url = os.environ.get("RAG_TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'identity.db'}")
    engine = database_engine(url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def foreign_keys(connection: object, record: object) -> None:
            connection.execute("PRAGMA foreign_keys=ON")  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    yield IdentityService(engine, CredentialCipher({"test": secrets.token_bytes(32)}, "test"))
    Base.metadata.drop_all(engine)
    engine.dispose()
