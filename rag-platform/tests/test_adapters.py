"""Offline boundary checks plus opt-in Compose integration in CI."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from rag_api.adapters import RuntimeProbe
from rag_api.readiness import DependencyName, ReadinessChecker
from rag_api.runtime import RuntimeSettings


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_artifact_probe_requires_existing_accessible_directory(
    runtime_env: dict[str, str], tmp_path: Path
) -> None:
    root = tmp_path / "artifacts"
    runtime_env["RAG_ARTIFACT_ROOT"] = str(root)
    probe = RuntimeProbe(DependencyName.ARTIFACTS, RuntimeSettings.from_env(runtime_env))
    assert not await probe.check()
    root.mkdir()
    assert await probe.check()
    with patch("rag_api.adapters.os.access", return_value=False):
        assert not await probe.check()
    assert list(root.iterdir()) == []


@pytest.mark.anyio
async def test_worker_probe_kills_and_reaps_timed_out_child(runtime_env: dict[str, str]) -> None:
    process = AsyncMock()
    process.returncode = None
    calls = 0

    async def wait() -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            await asyncio.Event().wait()
        return -9

    process.wait.side_effect = wait
    from unittest.mock import Mock

    process.kill = Mock()
    probe = RuntimeProbe(DependencyName.WORKER, RuntimeSettings.from_env(runtime_env))
    with patch("rag_api.adapters.asyncio.create_subprocess_exec", return_value=process):
        result = await ReadinessChecker([probe], timeout=0.1).check()
    assert result.dependencies[-1].status == "unavailable"
    process.kill.assert_called_once()
    assert calls == 2
