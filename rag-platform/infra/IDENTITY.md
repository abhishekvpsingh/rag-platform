# Identity foundation

T004 provides local owner bootstrap, database-backed sessions, encrypted credential
storage and an owner-only source authorization boundary. Connector OAuth, source
retrieval, user invitation, password recovery and the login UI are later work.

## Operator setup

Use the configured Python environment from the application README. Set
`RAG_DATABASE_URL` through a local secret environment, then from `rag-platform/`:

```bash
uv run --frozen alembic upgrade head
PYTHONPATH=services/api/src uv run --frozen python -m rag_api.identity.cli
```

Before bootstrap, set `RAG_CREDENTIAL_KEYS` to a JSON object mapping a key ID to a
base64-encoded, cryptographically random 32-byte key, and set
`RAG_ACTIVE_CREDENTIAL_KEY` to that ID. Generate/manage this key in your local
secret manager; never commit it. The CLI reads the owner's email and password
interactively. It never accepts a password argument or exposes a bootstrap HTTP
endpoint. A database singleton prevents repeated and concurrent setup, including
after restore. Passwords use argon2-cffi's maintained PasswordHasher defaults.

For Compose, configure these variables in the ignored `.env` and run migrations
and the bootstrap CLI inside the API container:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m rag_api.identity.cli
```

Recreate the API after changing its environment. Migrations are an explicit
operator step, not a race among API/worker startup processes. The API image
includes the migration files. Back up before upgrading; the initial migration
creates empty tables and performs no backfill. `alembic downgrade base` destroys
identity data and is appropriate only for disposable verification databases;
recover populated deployments by restoring a backup instead.

## HTTPS sessions

Set `RAG_AUTH_ENABLED=true` and `RAG_AUTH_ORIGIN` to the exact HTTPS browser origin
(no trailing slash). Start the configured `rag_api.main:runtime_app` entry point.
The existing HTTP Compose overview stays unauthenticated by default. Enable
sessions only behind an operator-configured HTTPS endpoint; cookies always have
Secure, HttpOnly, SameSite=Strict, host-only and root-path attributes. No insecure
cookie mode or permissive CORS is provided. The web login screen arrives later.

- `POST /api/v1/auth/login`: JSON email/password and matching Origin; returns a
  CSRF token and sets a random session cookie. Preserve CSRF in browser memory.
- `GET /api/v1/auth/me`: returns current user, membership tenant and role.
- `POST /api/v1/auth/logout`: matching Origin and `X-CSRF-Token`; revokes the
  persisted session and clears its cookie.

Sessions expire after eight hours and membership/account status is rechecked on
every access. Only session/CSRF hashes are persisted. Sensitive responses are
`no-store`; validation responses exclude submitted input. Login attempts have a
process-wide limit of ten per minute, including successful attempts. This is a
single-process foundation: multi-process/distributed deployment needs a shared
limiter and edge request-body limits. Multiple active tenant memberships fail
closed until an explicit tenant selection flow is implemented.

## Source isolation and key rotation

The internal service derives tenant context from persisted sessions. Composite
foreign keys prevent associating a connection/session/source identity with a
member of a different tenant. Administrative roles grant no source access.
`verify_source_identity` is a trusted adapter operation after provider proof,
not a browser claim. Source authorization requires a current owner mapping
(maximum verification horizon one hour) and an active connection. Unknown,
stale or non-owner identities fail closed. Shared ACL/group support is deferred.
Call authorization again at each future retrieval/evidence boundary; a returned
principal is not a reusable grant.

AES-256-GCM envelopes authenticate tenant and connection IDs. Keep old keys in
the keyring while rotating; set the new active ID and use `CredentialCipher.rotate`
to re-encrypt rows transactionally. Rotation is a tested primitive, not an
implemented bulk rotation command. Keep old keys available for retained backups.
Audit events contain fixed action names, actor/tenant IDs and timestamps only.
RLS is not yet enabled: tenant repositories and composite constraints are the
current enforcement, so database credentials remain privileged server secrets.

## Verification and recovery

```bash
PYTHONPATH=services/api/src uv run --frozen python scripts/verify_identity.py
```

Requires Docker and uses a newly named disposable PostgreSQL 17 container with a
random password and loopback-only ephemeral port. It removes only that container
and its anonymous volume. It runs the security suite on PostgreSQL, checks
migration/schema drift, downgrades/reapplies the empty schema, then dumps and
restores synthetic identity data into a separate database. Restored encrypted
credentials, bootstrap closure and session revocation are checked. CI runs this
in the Backend job. No existing application database/volume is used.

Real backups must be encrypted, access controlled, and retain the matching
credential keyring separately. This smoke test is not a full production recovery
drill; future deletion/tombstone replay must be implemented before retrieval is
served from restored document data.
