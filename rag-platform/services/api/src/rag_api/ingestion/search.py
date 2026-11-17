"""Idempotent OpenSearch staging; visibility is gated by authoritative DB generations."""

import hashlib
import json
from collections.abc import Callable

import httpx

from rag_api.ingestion.chunking import Chunk
from rag_api.ingestion.embeddings import EmbeddingConfig


class SearchFailure(Exception):
    pass


class OpenSearchIndex:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def stage(
        self,
        tenant: str,
        document: str,
        revision: str,
        generation: int,
        connection: str,
        config: EmbeddingConfig,
        chunks: list[Chunk],
        vectors: list[list[float]],
        checkpoint: Callable[[], bool] | None = None,
    ) -> str:
        index = "rag-" + hashlib.sha256(f"{tenant}/{config.fingerprint}".encode()).hexdigest()[:40]
        mapping = {
            "settings": {"index": {"knn": True, "number_of_shards": 1, "number_of_replicas": 0}},
            "mappings": {
                "dynamic": "strict",
                "properties": {
                    **{
                        key: {"type": "keyword"}
                        for key in (
                            "tenant",
                            "document",
                            "revision",
                            "connection",
                            "model",
                            "locator",
                            "section",
                            "parent",
                        )
                    },
                    "generation": {"type": "long"},
                    "start": {"type": "integer"},
                    "end": {"type": "integer"},
                    "text": {"type": "text"},
                    "vector": {
                        "type": "knn_vector",
                        "dimension": config.dimensions,
                        "method": {"name": "hnsw", "engine": "lucene", "space_type": "cosinesimil"},
                    },
                },
            },
        }
        try:
            response = self.client.put("/" + index, json=mapping, timeout=15)
            if response.status_code not in {200, 201}:
                if (
                    response.status_code != 400
                    or response.json().get("error", {}).get("type")
                    != "resource_already_exists_exception"
                ):
                    raise SearchFailure("search_unavailable")
            for offset in range(0, len(chunks), 32):
                if checkpoint is not None and not checkpoint():
                    raise SearchFailure("work_invalidated")
                lines = []
                for chunk, vector in zip(
                    chunks[offset : offset + 32], vectors[offset : offset + 32], strict=True
                ):
                    lines.append(
                        json.dumps({"index": {"_index": index, "_id": revision + "-" + chunk.id}})
                    )
                    lines.append(
                        json.dumps(
                            {
                                "tenant": tenant,
                                "document": document,
                                "revision": revision,
                                "connection": connection,
                                "generation": generation,
                                "model": config.fingerprint,
                                **chunk.model_dump(exclude={"id"}),
                                "vector": vector,
                            }
                        )
                    )
                result = self.client.post(
                    "/_bulk",
                    content="\n".join(lines) + "\n",
                    headers={"Content-Type": "application/x-ndjson"},
                    timeout=15,
                )
                if result.status_code != 200 or result.json().get("errors", True):
                    raise SearchFailure("search_unavailable")
            refreshed = self.client.post("/" + index + "/_refresh", timeout=15)
            if refreshed.status_code != 200:
                raise SearchFailure("search_unavailable")
            return index
        except (httpx.HTTPError, ValueError, KeyError):
            raise SearchFailure("search_unavailable") from None
