"""Version-one extension boundaries, not implemented product capabilities.

All source/evidence access carries an authorization snapshot. Implementations must
revalidate that snapshot before access/publication; possession is not authorization.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AccessScope:
    tenant_id: str
    actor_id: str
    source_id: str
    authorization_version: str


@dataclass(frozen=True)
class ArtifactRef:
    tenant_id: str
    artifact_id: str
    sha256: str


@dataclass(frozen=True)
class Evidence:
    scope: AccessScope
    document_id: str
    revision_id: str
    processing_version: str
    locator: str
    text: str


@dataclass(frozen=True)
class Capabilities:
    contract_version: int
    implementation_version: str
    features: frozenset[str]


class Adapter(Protocol):
    @property
    def capabilities(self) -> Capabilities: ...


@dataclass(frozen=True)
class SourcePage:
    item_ids: tuple[str, ...]
    next_cursor: str | None


class SourceConnector(Adapter, Protocol):
    async def discover(self, scope: AccessScope, cursor: str | None) -> SourcePage: ...
    async def download(self, scope: AccessScope, item_id: str, revision: str) -> ArtifactRef: ...


class ArtifactStore(Adapter, Protocol):
    async def read(self, scope: AccessScope, ref: ArtifactRef, max_bytes: int) -> bytes: ...
    async def write(self, scope: AccessScope, content: bytes) -> ArtifactRef: ...


class Parser(Adapter, Protocol):
    async def parse(
        self, scope: AccessScope, ref: ArtifactRef, processing_version: str
    ) -> tuple[Evidence, ...]: ...


@dataclass(frozen=True)
class Embeddings:
    model_version: str
    vectors: tuple[tuple[float, ...], ...]


class EmbeddingProvider(Adapter, Protocol):
    async def embed(self, scope: AccessScope, texts: tuple[str, ...]) -> Embeddings: ...


class Reranker(Adapter, Protocol):
    async def rank(
        self, scope: AccessScope, query: str, evidence: tuple[Evidence, ...], limit: int
    ) -> tuple[Evidence, ...]: ...


class GenerationProvider(Adapter, Protocol):
    async def generate(
        self, scope: AccessScope, query: str, evidence: tuple[Evidence, ...], max_tokens: int
    ) -> str: ...


class SearchBackend(Adapter, Protocol):
    async def retrieve(
        self, scope: AccessScope, query: str, limit: int
    ) -> tuple[Evidence, ...]: ...


class GraphBackend(Adapter, Protocol):
    async def traverse(
        self, scope: AccessScope, evidence: tuple[Evidence, ...], max_hops: int, limit: int
    ) -> tuple[Evidence, ...]: ...


@dataclass(frozen=True)
class CapacityObservation:
    window_seconds: int
    sample_count: int
    queue_depth: int
    latency_p95_ms: float


class CapacityAdvisor(Adapter, Protocol):
    def recommend(self, observation: CapacityObservation) -> tuple[str, ...]: ...
