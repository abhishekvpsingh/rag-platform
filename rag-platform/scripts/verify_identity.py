"""Disposable PostgreSQL migration, isolation and restore exercise. No application volumes."""

import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import psycopg
from alembic import command
from alembic.config import Config
from rag_api.identity.crypto import CredentialCipher
from rag_api.identity.service import AccessDenied, IdentityService, database_engine
from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    name = "rag-identity-test-" + uuid4().hex[:12]
    password = secrets.token_urlsafe(32)
    env = {**os.environ, "POSTGRES_PASSWORD": password}
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-e",
            "POSTGRES_PASSWORD",
            "-p",
            "127.0.0.1::5432",
            "postgres:17.6-bookworm",
        ],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    try:
        port = (
            subprocess.check_output(["docker", "port", name, "5432"], text=True)
            .strip()
            .rsplit(":", 1)[1]
        )
        url = f"postgresql://postgres:{password}@127.0.0.1:{port}/postgres"
        for _ in range(60):
            try:
                with psycopg.connect(url, connect_timeout=2):
                    break
            except psycopg.OperationalError:
                time.sleep(1)
        else:
            raise RuntimeError("Disposable PostgreSQL did not become ready")
        with psycopg.connect(url, autocommit=True) as db:
            for database in ("identity_tests", "identity_source", "identity_restored"):
                db.execute(
                    psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(database))
                )
        subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_identity.py", "-q", "--tb=short"],
            cwd=ROOT,
            env={**env, "RAG_TEST_DATABASE_URL": url.rsplit("/", 1)[0] + "/identity_tests"},
            check=True,
        )
        source_url = url.rsplit("/", 1)[0] + "/identity_source"
        os.environ["RAG_DATABASE_URL"] = source_url
        config = Config(str(ROOT / "alembic.ini"))
        command.upgrade(config, "head")
        command.check(config)
        command.downgrade(config, "base")
        engine = database_engine(source_url)
        assert inspect(engine).get_table_names() == ["alembic_version"]
        command.upgrade(config, "head")
        cipher = CredentialCipher({"smoke": secrets.token_bytes(32)}, "smoke")
        service = IdentityService(engine, cipher)
        owner_password = secrets.token_urlsafe(32)
        service.bootstrap("restore@example.test", owner_password)
        tokens = service.login("restore@example.test", owner_password)
        secret = secrets.token_urlsafe(48)
        connection_id = service.add_connection(tokens.token, "google_drive", secret)
        service.logout(tokens.token, tokens.csrf)
        # Archive remains in memory and contains synthetic records only.
        archive = subprocess.check_output(
            ["docker", "exec", name, "pg_dump", "-U", "postgres", "-Fc", "identity_source"]
        )
        assert secret.encode() not in archive
        subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                name,
                "pg_restore",
                "-U",
                "postgres",
                "--exit-on-error",
                "-d",
                "identity_restored",
            ],
            input=archive,
            check=True,
        )
        restored_engine = database_engine(url.rsplit("/", 1)[0] + "/identity_restored")
        restored = IdentityService(restored_engine, cipher)
        fresh = restored.login("restore@example.test", owner_password)
        assert restored.credential(fresh.token, connection_id) == secret
        try:
            restored.authenticate(tokens.token)
        except AccessDenied:
            pass
        else:
            raise AssertionError("Restore resurrected a revoked session")
        try:
            restored.bootstrap("again@example.test", secrets.token_urlsafe(24))
        except AccessDenied:
            pass
        else:
            raise AssertionError("Restore reopened bootstrap")
        engine.dispose()
        restored_engine.dispose()
        print("PostgreSQL security suite, migration round trip, drift check and restore passed")
    finally:
        subprocess.run(["docker", "rm", "-f", "-v", name], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
