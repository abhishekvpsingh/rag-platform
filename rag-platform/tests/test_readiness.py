"""Health semantics and failure isolation with deterministic offline probe adapters."""

import asyncio
from dataclasses import dataclass
from typing import Literal

import httpx
import pytest
from rag_api.main import create_app
from rag_api.readiness import DependencyName, ReadinessChecker


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass
class FixtureProbe:
    name: DependencyName
    behavior: Literal["ready", "fail", "raise", "hang"] = "ready"
    cancelled: bool = False

    async def check(self) -> bool:
        if self.behavior == "raise":
            raise ConnectionError("amqp://private-user:private-password@broker")
        if self.behavior == "hang":
            try:
                await asyncio.Event().wait()
            finally:
                self.cancelled = True
        return self.behavior == "ready"


@pytest.mark.anyio
async def test_unconfigured_runtime_is_not_ready_but_remains_live() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        assert (await client.get("/health/live")).status_code == 200
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_configured"
    assert all(item["status"] == "not_configured" for item in response.json()["dependencies"])


@pytest.mark.anyio
async def test_all_required_adapters_must_pass_to_serve_ready() -> None:
    probes = [FixtureProbe(name) for name in DependencyName]
    checker = ReadinessChecker(probes)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(checker)), base_url="http://test"
    ) as client:
        assert (await client.get("/health/ready")).status_code == 200
        probes[0].behavior = "fail"
        response = await client.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["status"] == "unavailable"
        probes[0].behavior = "ready"
        assert (await client.get("/health/ready")).status_code == 200


@pytest.mark.anyio
async def test_failure_text_is_redacted_and_other_dependencies_are_still_checked() -> None:
    probes = [FixtureProbe(name) for name in DependencyName]
    probes[0].behavior = "raise"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(ReadinessChecker(probes))),
        base_url="http://test",
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert "private" not in response.text
    states = {item["name"]: item["status"] for item in response.json()["dependencies"]}
    assert states["postgres"] == "unavailable"
    assert states["rabbitmq"] == "ready"


@pytest.mark.anyio
async def test_hung_probes_are_cancelled_with_a_bounded_overall_wait() -> None:
    probes = [FixtureProbe(name, behavior="hang") for name in DependencyName]
    # All probes run concurrently; five serial 0.1-second deadlines exceed this bound.
    report = await asyncio.wait_for(ReadinessChecker(probes, timeout=0.1).check(), timeout=0.4)
    assert report.status == "unavailable"
    assert all(probe.cancelled for probe in probes)


@pytest.mark.anyio
async def test_request_cancellation_propagates_to_probes() -> None:
    probes = [FixtureProbe(name, behavior="hang") for name in DependencyName]
    task = asyncio.create_task(ReadinessChecker(probes).check())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert all(probe.cancelled for probe in probes)


def test_duplicate_probes_are_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        ReadinessChecker([FixtureProbe(DependencyName.POSTGRES)] * 2)
