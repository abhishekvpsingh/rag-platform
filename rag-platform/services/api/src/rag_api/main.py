"""Public, non-sensitive service metadata. Knowledge APIs arrive after authorization."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["rag-api"] = "rag-api"


class CapabilitiesResponse(BaseModel):
    stage: Literal["foundation"] = "foundation"
    connectors_available: bool = False
    answering_available: bool = False
    knowledge_graph_enabled: bool = False
    distributed_enabled: bool = False


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Platform API",
        version="0.1.0-dev",
        description="Development foundation. Source connections and answers are not available yet.",
    )

    @app.get("/health/live", response_model=HealthResponse, tags=["health"])
    def liveness() -> HealthResponse:
        """Report process liveness, not dependency readiness or ingestion completeness."""
        return HealthResponse()

    @app.get("/api/v1/capabilities", response_model=CapabilitiesResponse, tags=["platform"])
    def capabilities() -> CapabilitiesResponse:
        return CapabilitiesResponse()

    return app


app = create_app()
