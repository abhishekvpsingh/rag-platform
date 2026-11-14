"""Live runtime probes. Connection errors are redacted by ReadinessChecker."""

import asyncio
import os
import ssl
import sys
from dataclasses import dataclass

import aio_pika
import httpx
import psycopg

from rag_api.readiness import DependencyName, ReadinessChecker
from rag_api.runtime import RuntimeSettings


@dataclass
class RuntimeProbe:
    name: DependencyName
    settings: RuntimeSettings
    search_ca: str | None = None

    async def check(self) -> bool:
        settings = self.settings
        match self.name:
            case DependencyName.POSTGRES:
                async with await psycopg.AsyncConnection.connect(
                    settings.database_url.get_secret_value(), connect_timeout=3
                ) as connection:
                    async with connection.cursor() as cursor:
                        await cursor.execute("SELECT 1")
                        return await cursor.fetchone() == (1,)
            case DependencyName.RABBITMQ:
                broker_connection = await aio_pika.connect(
                    settings.broker_url.get_secret_value(), timeout=3
                )
                try:
                    channel = await broker_connection.channel()
                    await channel.close()
                    return True
                finally:
                    await broker_connection.close()
            case DependencyName.OPENSEARCH:
                context = ssl.create_default_context(cafile=self.search_ca)
                async with httpx.AsyncClient(
                    verify=context,
                    auth=(
                        settings.search_username.get_secret_value(),
                        settings.search_password.get_secret_value(),
                    ),
                    timeout=3,
                    trust_env=False,
                ) as client:
                    response = await client.get(settings.search_url + "/_cluster/health")
                    response.raise_for_status()
                    return response.json().get("status") in ("green", "yellow")
            case DependencyName.ARTIFACTS:
                root = settings.artifact_root
                return root.is_dir() and os.access(root, os.R_OK | os.W_OK | os.X_OK)
            case DependencyName.WORKER:
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "rag_api.worker_health",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                try:
                    return await process.wait() == 0
                finally:
                    if process.returncode is None:
                        process.kill()
                        await process.wait()
        return False


def runtime_checker(settings: RuntimeSettings, search_ca: str | None = None) -> ReadinessChecker:
    return ReadinessChecker(
        [RuntimeProbe(name, settings, search_ca) for name in DependencyName],
        timeout=settings.probe_timeout_seconds,
    )
