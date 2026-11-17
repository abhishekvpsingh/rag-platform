"""Operator-configured ingestion worker. External model use is explicit."""

import os
import ssl
from pathlib import Path

import httpx

from rag_api.ingestion.artifacts import LocalArtifacts
from rag_api.ingestion.embeddings import (
    CompatibleEmbeddings,
    Embedder,
    EmbeddingConfig,
    FixtureEmbeddings,
)
from rag_api.ingestion.search import OpenSearchIndex
from rag_api.ingestion.service import run_pipeline
from rag_api.jobs.service import JobService, Lease


def configured_embedder() -> Embedder:
    mode = os.environ.get("RAG_EMBEDDING_MODE", "")
    if mode == "fixture":
        return FixtureEmbeddings()
    if mode != "compatible":
        raise ValueError("Embedding provider not configured")
    config = EmbeddingConfig(
        os.environ["RAG_EMBEDDING_MODEL"],
        os.environ["RAG_EMBEDDING_REVISION"],
        int(os.environ["RAG_EMBEDDING_DIMENSIONS"]),
    )
    return CompatibleEmbeddings(
        config,
        os.environ["RAG_EMBEDDING_ENDPOINT"],
        os.environ["RAG_EMBEDDING_KEY"],
        frozenset(os.environ["RAG_EMBEDDING_ALLOWED_ORIGINS"].split(",")),
    )


def execute_ingestion(jobs: JobService, lease: Lease) -> None:
    try:
        embedder = configured_embedder()
        ca = os.environ.get("RAG_SEARCH_CA")
        context = ssl.create_default_context(cafile=ca if ca else None)
        with httpx.Client(
            base_url=os.environ["RAG_SEARCH_URL"],
            verify=context,
            auth=(os.environ["RAG_SEARCH_USERNAME"], os.environ["RAG_SEARCH_PASSWORD"]),
            follow_redirects=False,
            trust_env=False,
        ) as client:
            run_pipeline(
                jobs.engine,
                lease,
                LocalArtifacts(Path(os.environ["RAG_ARTIFACT_ROOT"])),
                embedder,
                OpenSearchIndex(client),
            )
    except (KeyError, ValueError):
        jobs.fail(lease, transient=False)
    except Exception:
        jobs.fail(lease, transient=True)
