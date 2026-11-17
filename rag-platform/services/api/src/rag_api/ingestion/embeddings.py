"""Explicitly configured, bounded embedding transport; no automatic external fallback."""

import hashlib
import math
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

import httpx


class ProviderFailure(Exception):
    def __init__(self, transient: bool) -> None:
        super().__init__("embedding_unavailable" if transient else "embedding_rejected")
        self.transient = transient


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str
    revision: str
    dimensions: int
    max_input_bytes: int = 2048
    batch_size: int = 16

    def __post_init__(self) -> None:
        if not self.model or not self.revision or not 1 <= self.dimensions <= 4096:
            raise ValueError("Invalid embedding configuration")
        if not 256 <= self.max_input_bytes <= 8192 or not 1 <= self.batch_size <= 32:
            raise ValueError("Invalid embedding limits")

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(
            f"{self.model}/{self.revision}/{self.dimensions}".encode()
        ).hexdigest()


class Embedder(Protocol):
    config: EmbeddingConfig

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def validate_vectors(value: list[list[float]], count: int, dimensions: int) -> list[list[float]]:
    if len(value) != count:
        raise ProviderFailure(False)
    for vector in value:
        if len(vector) != dimensions or any(not math.isfinite(x) for x in vector):
            raise ProviderFailure(False)
        norm = math.sqrt(sum(x * x for x in vector))
        if not math.isfinite(norm) or norm == 0:
            raise ProviderFailure(False)
    return value


class CompatibleEmbeddings:
    def __init__(
        self,
        config: EmbeddingConfig,
        endpoint: str,
        api_key: str,
        allowed_origins: frozenset[str],
        client: httpx.Client | None = None,
    ) -> None:
        parsed = urlsplit(endpoint)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if (
            parsed.scheme != "https"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Embedding endpoint must be an approved HTTPS URL")
        if origin not in allowed_origins or not api_key:
            raise ValueError("Embedding provider not approved")
        self.config = config
        self.endpoint = endpoint.rstrip("/") + "/embeddings"
        self.api_key = api_key
        self.client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or len(texts) > self.config.batch_size:
            raise ProviderFailure(False)
        if any(not text or len(text.encode()) > self.config.max_input_bytes for text in texts):
            raise ProviderFailure(False)
        try:
            with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as owned:
                client = self.client or owned
                with client.stream(
                    "POST",
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.config.model,
                        "input": texts,
                        "dimensions": self.config.dimensions,
                    },
                    timeout=15,
                    follow_redirects=False,
                ) as response:
                    if response.status_code != 200:
                        raise ProviderFailure(
                            response.status_code in {408, 429} or response.status_code >= 500
                        )
                    body = bytearray()
                    for part in response.iter_bytes():
                        body.extend(part)
                        if len(body) > 8 * 1024 * 1024:
                            raise ProviderFailure(False)
            import json

            payload = json.loads(body)
            records = payload["data"]
            if len(records) != len(texts) or sorted(x["index"] for x in records) != list(
                range(len(texts))
            ):
                raise ProviderFailure(False)
            vectors = [
                [float(v) for v in record["embedding"]]
                for record in sorted(records, key=lambda x: x["index"])
            ]
            return validate_vectors(vectors, len(texts), self.config.dimensions)
        except ProviderFailure:
            raise
        except httpx.HTTPError:
            raise ProviderFailure(True) from None
        except (ValueError, TypeError, KeyError, OverflowError):
            raise ProviderFailure(False) from None


class FixtureEmbeddings:
    """Deterministic offline fixture only; never a semantic retrieval model."""

    config = EmbeddingConfig("fixture-sha256", "v1", 8)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [
            [(b + 1) / 256 for b in hashlib.sha256(text.encode()).digest()[:8]] for text in texts
        ]
