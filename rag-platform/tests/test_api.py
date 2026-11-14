"""Exercise real ASGI routing without credentials or network services."""

import httpx
import pytest
from rag_api.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_process_liveness() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "rag-api"}


@pytest.mark.anyio
async def test_no_unimplemented_features_are_advertised() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/capabilities")
        missing = await client.post("/api/v1/questions", json={"question": "Leave policy?"})
    assert response.status_code == 200
    assert response.json() == {
        "stage": "foundation",
        "connectors_available": False,
        "answering_available": False,
        "knowledge_graph_enabled": False,
        "distributed_enabled": False,
    }
    assert missing.status_code == 404


@pytest.mark.anyio
async def test_openapi_declares_public_endpoints() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        schema = (await client.get("/openapi.json")).json()
    assert set(schema["paths"]) == {
        "/health/live",
        "/health/ready",
        "/api/v1/capabilities",
    }
