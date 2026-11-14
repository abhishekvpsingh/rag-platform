"""Transactional identity operations; no caller-supplied tenant on authenticated paths."""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rag_api.identity.crypto import CredentialCipher
from rag_api.identity.models import (
    AuditEvent,
    Bootstrap,
    Connection,
    Membership,
    SessionRecord,
    SourceIdentity,
    Tenant,
    User,
)


def database_engine(url: str) -> Engine:
    parsed = make_url(url)
    if parsed.drivername == "postgresql":
        parsed = parsed.set(drivername="postgresql+psycopg")
    options = (
        {"connect_timeout": 5, "options": "-c statement_timeout=5000 -c lock_timeout=5000"}
        if parsed.get_backend_name() == "postgresql"
        else {}
    )
    return create_engine(parsed, hide_parameters=True, pool_pre_ping=True, connect_args=options)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def now() -> datetime:
    return datetime.now(UTC)


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class AccessDenied(Exception):
    """Deliberately carries no identifiers or secrets."""


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    user_id: str
    role: str


@dataclass(frozen=True)
class SessionTokens:
    token: str = field(repr=False)
    csrf: str = field(repr=False)


class IdentityService:
    def __init__(self, engine: Engine, cipher: CredentialCipher, lifetime: int = 28800) -> None:
        self.engine = engine
        self.cipher = cipher
        self.lifetime = lifetime
        self.passwords = PasswordHasher()
        self.dummy_hash = self.passwords.hash(secrets.token_urlsafe(32))

    @staticmethod
    def audit(db: Session, principal: Principal, action: str) -> None:
        # Only internal fixed event names, no request bodies or credential metadata.
        db.add(
            AuditEvent(
                id=str(uuid4()),
                tenant_id=principal.tenant_id,
                actor_id=principal.user_id,
                action=action,
                occurred_at=now(),
            )
        )

    def bootstrap(self, email: str, password: str) -> Principal:
        """Called exclusively by a local operator CLI; the database arbitrates concurrency."""
        if not 12 <= len(password) <= 256 or not 3 <= len(email) <= 254 or "@" not in email:
            raise ValueError("Invalid owner input")
        principal = Principal(str(uuid4()), str(uuid4()), "owner")
        hashed = self.passwords.hash(password)
        try:
            with Session(self.engine) as db, db.begin():
                db.add(Tenant(id=principal.tenant_id))
                db.add(
                    User(
                        id=principal.user_id,
                        email=email.strip().lower(),
                        password_hash=hashed,
                        active=True,
                    )
                )
                db.flush()
                db.add(
                    Membership(
                        tenant_id=principal.tenant_id,
                        user_id=principal.user_id,
                        role="owner",
                        active=True,
                    )
                )
                db.flush()
                db.add(Bootstrap(id=1, tenant_id=principal.tenant_id))
                self.audit(db, principal, "owner.bootstrap")
        except IntegrityError:
            raise AccessDenied() from None
        return principal

    def login(self, email: str, password: str) -> SessionTokens:
        with Session(self.engine) as db, db.begin():
            user = db.scalar(select(User).where(User.email == email.strip().lower()))
            try:
                self.passwords.verify(user.password_hash if user else self.dummy_hash, password)
            except VerificationError:
                raise AccessDenied() from None
            if user is None or not user.active:
                raise AccessDenied()
            memberships = list(
                db.scalars(
                    select(Membership).where(
                        Membership.user_id == user.id, Membership.active.is_(True)
                    )
                )
            )
            # Explicit tenant switching is future work; ambiguous identity fails closed.
            if len(memberships) != 1:
                raise AccessDenied()
            membership = memberships[0]
            if self.passwords.check_needs_rehash(user.password_hash):
                user.password_hash = self.passwords.hash(password)
            tokens = SessionTokens(secrets.token_urlsafe(32), secrets.token_urlsafe(32))
            db.add(
                SessionRecord(
                    token_hash=digest(tokens.token),
                    tenant_id=membership.tenant_id,
                    user_id=user.id,
                    csrf_hash=digest(tokens.csrf),
                    expires_at=now() + timedelta(seconds=self.lifetime),
                    revoked=False,
                )
            )
            self.audit(
                db, Principal(membership.tenant_id, user.id, membership.role), "session.login"
            )
            return tokens

    @staticmethod
    def resolve(db: Session, token: str, csrf: str | None = None) -> Principal:
        session = db.get(SessionRecord, digest(token))
        if session is None or session.revoked or utc(session.expires_at) <= now():
            raise AccessDenied()
        if csrf is not None and not secrets.compare_digest(session.csrf_hash, digest(csrf)):
            raise AccessDenied()
        membership = db.get(Membership, (session.tenant_id, session.user_id))
        user = db.get(User, session.user_id)
        if membership is None or not membership.active or user is None or not user.active:
            raise AccessDenied()
        return Principal(membership.tenant_id, membership.user_id, membership.role)

    def authenticate(self, token: str, csrf: str | None = None) -> Principal:
        with Session(self.engine) as db:
            return self.resolve(db, token, csrf)

    def logout(self, token: str, csrf: str) -> None:
        with Session(self.engine) as db, db.begin():
            principal = self.resolve(db, token, csrf)
            record = db.get(SessionRecord, digest(token))
            assert record is not None
            record.revoked = True
            self.audit(db, principal, "session.logout")

    def add_connection(self, token: str, provider: str, credential: str) -> str:
        """Internal connector boundary, not an HTTP endpoint or implemented connector."""
        if provider not in {"google_drive", "onedrive"}:
            raise ValueError("Unsupported provider")
        with Session(self.engine) as db, db.begin():
            principal = self.resolve(db, token)
            connection_id = str(uuid4())
            db.add(
                Connection(
                    tenant_id=principal.tenant_id,
                    id=connection_id,
                    owner_id=principal.user_id,
                    provider=provider,
                    credential=self.cipher.encrypt(credential, principal.tenant_id, connection_id),
                    active=True,
                )
            )
            self.audit(db, principal, "connection.created")
            return connection_id

    def verify_source_identity(
        self, token: str, connection_id: str, subject: str, valid_until: datetime
    ) -> None:
        """Trusted adapter only, after provider proof; never accepts browser verification claims."""
        if (
            not subject
            or len(subject) > 255
            or not now() < utc(valid_until) <= now() + timedelta(hours=1)
        ):
            raise ValueError("Invalid source verification")
        with Session(self.engine) as db, db.begin():
            principal = self.resolve(db, token)
            connection = db.get(Connection, (principal.tenant_id, connection_id))
            if (
                connection is None
                or not connection.active
                or connection.owner_id != principal.user_id
            ):
                raise AccessDenied()
            db.merge(
                SourceIdentity(
                    tenant_id=principal.tenant_id,
                    connection_id=connection_id,
                    user_id=principal.user_id,
                    subject=subject,
                    verified_until=valid_until,
                )
            )
            self.audit(db, principal, "source_identity.verified")

    def authorize_source(self, token: str, connection_id: str) -> Principal:
        """Owner-only policy; membership/admin privileges never imply provider access."""
        with Session(self.engine) as db, db.begin():
            principal = self.resolve(db, token)
            connection = db.get(Connection, (principal.tenant_id, connection_id))
            identity = db.get(
                SourceIdentity, (principal.tenant_id, connection_id, principal.user_id)
            )
            allowed = (
                connection is not None
                and connection.active
                and connection.owner_id == principal.user_id
                and identity is not None
                and utc(identity.verified_until) > now()
            )
            self.audit(db, principal, "source.allowed" if allowed else "source.denied")
        if not allowed:
            raise AccessDenied()
        return principal

    def credential(self, token: str, connection_id: str) -> str:
        # This service capability is owner scoped even before content verification.
        with Session(self.engine) as db:
            principal = self.resolve(db, token)
            connection = db.get(Connection, (principal.tenant_id, connection_id))
            if (
                connection is None
                or not connection.active
                or connection.owner_id != principal.user_id
            ):
                raise AccessDenied()
            return self.cipher.decrypt(connection.credential, principal.tenant_id, connection_id)
