"""Bounded dependency health contract, separate from process liveness."""

import asyncio
from collections.abc import Sequence
from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel


class DependencyName(StrEnum):
    POSTGRES = "postgres"
    RABBITMQ = "rabbitmq"
    OPENSEARCH = "opensearch"
    ARTIFACTS = "artifacts"
    WORKER = "worker"


class DependencyProbe(Protocol):
    """Adapters must perform a real, non-mutating check and release their resources.

    Do not probe arbitrary user-supplied URLs. Implementations must propagate cancellation
    and avoid logging credentials. A successful connection is not an authorization check.
    """

    @property
    def name(self) -> DependencyName: ...

    async def check(self) -> bool: ...


class DependencyHealth(BaseModel):
    name: DependencyName
    status: Literal["ready", "unavailable", "not_configured"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unavailable", "not_configured"]
    dependencies: list[DependencyHealth]


class ReadinessChecker:
    """Require every runtime dependency; incomplete wiring cannot report readiness."""

    def __init__(self, probes: Sequence[DependencyProbe] = (), timeout: float = 2) -> None:
        if not 0.1 <= timeout <= 10:
            raise ValueError("Probe timeout must be between 0.1 and 10 seconds")
        self._probes = {probe.name: probe for probe in probes}
        if len(self._probes) != len(probes):
            raise ValueError("Duplicate dependency probe")
        self._timeout = timeout

    async def _check(self, name: DependencyName) -> DependencyHealth:
        probe = self._probes.get(name)
        if probe is None:
            return DependencyHealth(name=name, status="not_configured")
        try:
            ready = await asyncio.wait_for(probe.check(), timeout=self._timeout)
        except Exception:
            # Exception text may contain connection URLs or passwords. Never return it.
            ready = False
        return DependencyHealth(name=name, status="ready" if ready else "unavailable")

    async def check(self) -> ReadinessResponse:
        dependencies = list(await asyncio.gather(*(self._check(name) for name in DependencyName)))
        if any(item.status == "unavailable" for item in dependencies):
            status: Literal["ready", "unavailable", "not_configured"] = "unavailable"
        elif any(item.status == "not_configured" for item in dependencies):
            status = "not_configured"
        else:
            status = "ready"
        return ReadinessResponse(status=status, dependencies=dependencies)
