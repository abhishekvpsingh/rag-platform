"""Public, non-sensitive service metadata. Knowledge APIs arrive after authorization."""

from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.responses import JSONResponse

from rag_api.readiness import ReadinessChecker, ReadinessResponse


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["rag-api"] = "rag-api"


class CapabilitiesResponse(BaseModel):
    stage: Literal["foundation"] = "foundation"
    connectors_available: bool = False
    answering_available: bool = False
    knowledge_graph_enabled: bool = False
    distributed_enabled: bool = False


def create_app(readiness: ReadinessChecker | None = None) -> FastAPI:
    checker = readiness if readiness is not None else ReadinessChecker()
    app = FastAPI(
        title="RAG Platform API",
        version="0.1.0-dev",
        description="Development foundation. Source connections and answers are not available yet.",
    )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
        # Validation details can contain raw password/token input.
        return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    @app.get("/health/live", response_model=HealthResponse, tags=["health"])
    def liveness() -> HealthResponse:
        """Report process liveness, not dependency readiness or ingestion completeness."""
        return HealthResponse()

    @app.get(
        "/health/ready",
        response_model=ReadinessResponse,
        responses={503: {"model": ReadinessResponse}},
        tags=["health"],
    )
    async def readiness_status() -> JSONResponse:
        """Fail closed until every required runtime adapter is wired and responding."""
        report = await checker.check()
        return JSONResponse(
            status_code=200 if report.status == "ready" else 503,
            content=report.model_dump(mode="json"),
        )

    @app.get("/api/v1/capabilities", response_model=CapabilitiesResponse, tags=["platform"])
    def capabilities() -> CapabilitiesResponse:
        return CapabilitiesResponse()

    return app


app = create_app()


def runtime_app() -> FastAPI:
    """Explicit configured entry point: invalid configuration fails startup safely."""
    import os

    from rag_api.adapters import runtime_checker
    from rag_api.runtime import RuntimeSettings

    settings = RuntimeSettings.from_env(os.environ)
    app = create_app(runtime_checker(settings, os.environ.get("RAG_SEARCH_CA")))
    if os.environ.get("RAG_AUTH_ENABLED") == "true":
        from rag_api.identity.cli import configured_origin, configured_service
        from rag_api.identity.http import auth_router

        app.include_router(
            auth_router(configured_service(os.environ), configured_origin(os.environ))
        )
    return app
