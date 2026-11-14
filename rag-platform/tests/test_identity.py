"""Security suite also run against disposable PostgreSQL in CI."""

import os
import secrets
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from rag_api.identity.crypto import CredentialCipher
from rag_api.identity.http import COOKIE, auth_router
from rag_api.identity.models import (
    AuditEvent,
    Base,
    Bootstrap,
    Connection,
    Membership,
    SessionRecord,
    SourceIdentity,
    Tenant,
    User,
)
from rag_api.identity.service import AccessDenied, IdentityService, database_engine, digest, now
from rag_api.main import create_app
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.fixture
def service(tmp_path: Path) -> Iterator[IdentityService]:
    url = os.environ.get("RAG_TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'identity.db'}")
    engine = database_engine(url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def foreign_keys(connection: object, record: object) -> None:
            connection.execute("PRAGMA foreign_keys=ON")  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    yield IdentityService(engine, CredentialCipher({"test": secrets.token_bytes(32)}, "test"))
    Base.metadata.drop_all(engine)
    engine.dispose()


def owner(service: IdentityService) -> str:
    password = secrets.token_urlsafe(24)
    service.bootstrap("owner@example.test", password)
    return service.login("owner@example.test", password).token


def member(service: IdentityService, tenant_id: str | None = None) -> str:
    user_id, password = str(uuid4()), secrets.token_urlsafe(24)
    with Session(service.engine) as db, db.begin():
        if tenant_id is None:
            tenant_id = str(uuid4())
            db.add(Tenant(id=tenant_id))
        db.add(
            User(
                id=user_id,
                email=f"{user_id}@example.test",
                password_hash=service.passwords.hash(password),
                active=True,
            )
        )
        db.flush()
        db.add(Membership(tenant_id=tenant_id, user_id=user_id, role="admin", active=True))
    return service.login(f"{user_id}@example.test", password).token


def test_bootstrap_atomic_one_time(service: IdentityService) -> None:
    def attempt(index: int) -> bool:
        try:
            service.bootstrap(f"owner{index}@example.test", secrets.token_urlsafe(24))
            return True
        except AccessDenied:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(attempt, range(2))) == 1
    with pytest.raises(AccessDenied):
        service.bootstrap("third@example.test", secrets.token_urlsafe(24))
    with Session(service.engine) as db:
        for model in (Bootstrap, User, Tenant, Membership):
            assert db.scalar(select(func.count()).select_from(model)) == 1


def test_source_and_tenant_isolation(service: IdentityService) -> None:
    token = owner(service)
    principal = service.authenticate(token)
    same_tenant, other_tenant = member(service, principal.tenant_id), member(service)
    secret = secrets.token_urlsafe(48)
    connection_id = service.add_connection(token, "google_drive", secret)
    with pytest.raises(AccessDenied):
        service.authorize_source(token, connection_id)
    service.verify_source_identity(token, connection_id, "subject", now() + timedelta(minutes=5))
    assert service.authorize_source(token, connection_id) == principal
    assert service.credential(token, connection_id) == secret
    for forbidden in (same_tenant, other_tenant):
        for operation in (service.authorize_source, service.credential):
            with pytest.raises(AccessDenied):
                operation(forbidden, connection_id)
        with pytest.raises(AccessDenied):
            service.verify_source_identity(
                forbidden, connection_id, "subject", now() + timedelta(minutes=5)
            )
    with Session(service.engine) as db, db.begin():
        connection = db.get(Connection, (principal.tenant_id, connection_id))
        assert connection is not None and secret not in connection.credential
        identity = db.get(SourceIdentity, (principal.tenant_id, connection_id, principal.user_id))
        assert identity is not None
        identity.verified_until = now() - timedelta(seconds=1)
    with pytest.raises(AccessDenied):
        service.authorize_source(token, connection_id)
    with Session(service.engine) as db:
        assert "source.denied" in list(db.scalars(select(AuditEvent.action)))
    other = service.authenticate(other_tenant)
    with pytest.raises(IntegrityError), Session(service.engine) as db, db.begin():
        db.add(
            Connection(
                tenant_id=principal.tenant_id,
                id=str(uuid4()),
                owner_id=other.user_id,
                provider="google_drive",
                credential="unusable",
                active=True,
            )
        )


def test_session_lifecycle(service: IdentityService) -> None:
    password = secrets.token_urlsafe(24)
    principal = service.bootstrap("owner@example.test", password)
    first = service.login("owner@example.test", password)
    with pytest.raises(AccessDenied):
        service.logout(first.token, "wrong")
    service.logout(first.token, first.csrf)
    with pytest.raises(AccessDenied):
        service.authenticate(first.token)
    second = service.login("owner@example.test", password)
    with Session(service.engine) as db, db.begin():
        record = db.get(SessionRecord, digest(second.token))
        assert record is not None and record.token_hash != second.token
        record.expires_at = now() - timedelta(seconds=1)
    with pytest.raises(AccessDenied):
        service.authenticate(second.token)
    third = service.login("owner@example.test", password)
    with Session(service.engine) as db, db.begin():
        membership = db.get(Membership, (principal.tenant_id, principal.user_id))
        assert membership is not None
        membership.active = False
    with pytest.raises(AccessDenied):
        service.authenticate(third.token)
    with pytest.raises(AccessDenied):
        service.login("owner@example.test", password)


def test_cipher_rotation_binding_tampering() -> None:
    old, new = secrets.token_bytes(32), secrets.token_bytes(32)
    original = CredentialCipher({"old": old}, "old")
    rotating = CredentialCipher({"old": old, "new": new}, "new")
    secret = secrets.token_urlsafe(32)
    envelope = original.encrypt(secret, "tenant-a", "connection-a")
    assert secret not in envelope and secret not in repr(original)
    for tenant, connection in [("tenant-b", "connection-a"), ("tenant-a", "connection-b")]:
        with pytest.raises(ValueError, match="Credential unavailable"):
            rotating.decrypt(envelope, tenant, connection)
    rotated = rotating.rotate(envelope, "tenant-a", "connection-a")
    assert (
        CredentialCipher({"new": new}, "new").decrypt(rotated, "tenant-a", "connection-a") == secret
    )
    with pytest.raises(ValueError):
        original.decrypt(rotated, "tenant-a", "connection-a")
    with pytest.raises(ValueError):
        original.decrypt(envelope[:-5] + "bad", "tenant-a", "connection-a")


def test_http_security(service: IdentityService) -> None:
    password = secrets.token_urlsafe(24)
    service.bootstrap("owner@example.test", password)
    app = create_app()
    app.include_router(auth_router(service, "https://app.example.test"))
    with TestClient(app, base_url="https://app.example.test") as client:
        body = {"email": "owner@example.test", "password": password}
        assert client.post("/api/v1/auth/login", json=body).status_code == 403
        headers = {"Origin": "https://app.example.test"}
        response = client.post("/api/v1/auth/login", json=body, headers=headers)
        assert response.status_code == 200
        cookie = response.headers["set-cookie"]
        assert all(flag in cookie for flag in ("Secure", "HttpOnly", "SameSite=strict", COOKIE))
        assert "Domain=" not in cookie
        assert client.get("/api/v1/auth/me").status_code == 200
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 403
        assert (
            client.post(
                "/api/v1/auth/logout",
                headers={**headers, "x-csrf-token": response.json()["csrf_token"]},
            ).status_code
            == 204
        )
        assert client.get("/api/v1/auth/me").status_code == 401
        invalid = client.post("/api/v1/auth/login", json={**body, "email": "x"}, headers=headers)
        assert invalid.status_code == 422 and password not in invalid.text
        for _ in range(9):
            assert (
                client.post(
                    "/api/v1/auth/login",
                    json={**body, "password": secrets.token_urlsafe(24)},
                    headers=headers,
                ).status_code
                == 401
            )
        assert client.post("/api/v1/auth/login", json=body, headers=headers).status_code == 429


def test_disabled_connection_and_account_fail_closed(service: IdentityService) -> None:
    token = owner(service)
    principal = service.authenticate(token)
    connection_id = service.add_connection(token, "onedrive", secrets.token_urlsafe(32))
    service.verify_source_identity(token, connection_id, "subject", now() + timedelta(minutes=5))
    with Session(service.engine) as db, db.begin():
        connection = db.get(Connection, (principal.tenant_id, connection_id))
        assert connection is not None
        connection.active = False
    for operation in (service.credential, service.authorize_source):
        with pytest.raises(AccessDenied):
            operation(token, connection_id)
    with Session(service.engine) as db, db.begin():
        user = db.get(User, principal.user_id)
        assert user is not None
        user.active = False
    with pytest.raises(AccessDenied):
        service.authenticate(token)
    with pytest.raises(AccessDenied):
        service.add_connection(token, "onedrive", secrets.token_urlsafe(32))


def test_configuration_and_tokens_do_not_render_secrets() -> None:
    from rag_api.identity.cli import configured_origin, configured_service
    from rag_api.identity.service import SessionTokens

    secret = secrets.token_urlsafe(32)
    assert secret not in repr(SessionTokens(secret, secret))
    with pytest.raises(ValueError) as invalid:
        configured_service({"RAG_CREDENTIAL_KEYS": secret})
    assert secret not in str(invalid.value)
    for origin in (
        "http://localhost:3000",
        "https://app.example.test/",
        "https://user@app.example.test",
    ):
        with pytest.raises(ValueError):
            configured_origin({"RAG_AUTH_ORIGIN": origin})
