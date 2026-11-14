"""Synthetic shared runtime settings."""

import secrets
from urllib.parse import urlunsplit

import pytest


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
