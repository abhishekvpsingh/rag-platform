"""Opt-in synthetic persistence exercise executed inside the development API container."""

import asyncio
import os
import sys

import aio_pika
import httpx
import psycopg
from rag_api.runtime import RuntimeSettings


async def main(mode: str) -> None:
    settings = RuntimeSettings.from_env(os.environ)
    write = mode == "write"
    assert mode in ("write", "read")
    async with await psycopg.AsyncConnection.connect(
        settings.database_url.get_secret_value(), connect_timeout=3
    ) as connection:
        async with connection.cursor() as cursor:
            if write:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS runtime_smoke (id integer PRIMARY KEY)"
                )
                await cursor.execute("INSERT INTO runtime_smoke VALUES (42) ON CONFLICT DO NOTHING")
            await cursor.execute("SELECT id FROM runtime_smoke")
            assert await cursor.fetchone() == (42,)
    path = settings.artifact_root / "runtime-smoke.txt"
    if write:
        path.write_text("synthetic runtime persistence fixture\n")
    assert path.read_text() == "synthetic runtime persistence fixture\n"
    import ssl

    async with httpx.AsyncClient(
        verify=ssl.create_default_context(cafile=os.environ["RAG_SEARCH_CA"]),
        auth=(
            settings.search_username.get_secret_value(),
            settings.search_password.get_secret_value(),
        ),
        timeout=10,
        trust_env=False,
    ) as client:
        denied = await client.get(settings.search_url + "/_cluster/health", auth=None)
        assert denied.status_code == 401
        users = await client.get(settings.search_url + "/_plugins/_security/api/internalusers")
        users.raise_for_status()
        assert set(users.json()) == {"admin"}
        url = settings.search_url + "/runtime-smoke/_doc/42"
        if write:
            response = await client.put(url, json={"synthetic": True})
            response.raise_for_status()
        response = await client.get(url)
        response.raise_for_status()
        assert response.json()["_source"] == {"synthetic": True}
    broker_connection = await aio_pika.connect(settings.broker_url.get_secret_value(), timeout=3)
    async with broker_connection:
        channel = await broker_connection.channel(publisher_confirms=True)
        queue = await channel.declare_queue("runtime-smoke", durable=True)
        if write:
            await channel.default_exchange.publish(
                aio_pika.Message(b"synthetic", delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=queue.name,
            )
        message = await queue.get(timeout=5)
        assert message is not None and message.body == b"synthetic"
        await message.reject(requeue=True)
    print("PostgreSQL, artifacts, authenticated TLS search, durable RabbitMQ state: passed")


if __name__ == "__main__":
    try:
        asyncio.run(main(sys.argv[1]))
    except Exception:
        raise SystemExit(
            "Runtime persistence verification failed; connection details redacted"
        ) from None
