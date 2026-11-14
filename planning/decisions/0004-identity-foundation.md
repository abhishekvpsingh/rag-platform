# ADR 0004: Identity foundation and local owner bootstrap

- Status: accepted for T004.
- Context: owner-only product development needs persisted identity and tenant
  boundaries before connectors or retrieval; enterprise SSO remains T018.
- Decision: SQLAlchemy 2/Alembic with composite tenant foreign keys; local terminal
  bootstrap guarded by a database singleton; argon2-cffi password hashing;
  opaque database sessions with hashed tokens, eight-hour expiry, secure cookies,
  exact Origin and CSRF validation. AES-GCM credentials bind tenant/connection
  IDs and include a key ID for staged rotation. Fixed-schema audit events omit
  arbitrary metadata and raw inputs. Source mappings expire within one hour.
- Alternatives: signed stateless sessions complicate immediate revocation;
  public bootstrap increases attack surface; custom password cryptography is
  prohibited; OIDC requires external registration and belongs to enterprise work.
- Consequences: HTTPS is required for interactive authentication. Existing HTTP
  overview runs without auth routes until explicitly configured. RLS and shared
  rate limiting remain later hardening; current repositories authenticate tenant
  membership and database constraints prevent cross-tenant relationships. Source
  admins are not treated as content owners. No source ACL/group claims are made.
- Validation: behavioral tests on SQLite and real PostgreSQL; migration/drift and
  dump/restore checks in `scripts/verify_identity.py`. Results tracked in PROGRESS.
- Related: T004, SECURITY_AND_PERMISSIONS, DATA_MODEL.
