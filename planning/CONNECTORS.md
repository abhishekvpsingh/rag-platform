# Connector specification

## Contract

Each adapter declares supported account types, file/export types, permission semantics, versioning, delta support, and limitations. Implement connect/refresh/disconnect, discover pages, fetch metadata/content, read effective access or verify access, enumerate changes, resume cursor, and health diagnostics.

Every call accepts connection scope, cancellation, bounded timeout, and a redacted trace context. Normalize errors into auth-required, forbidden, not-found, throttled, transient, unsupported, and permanent. Respect Retry-After and maintain per-provider/account concurrency limits.

## Google Drive

Initial scope: My Drive with delegated OAuth. Use stable file IDs, incremental change tokens, explicit folder selection, and native Google document export. Handle shortcuts without recursive cycles or unauthorized target access. Track moves and trashed files. Record export format and revision fingerprint when native export lacks a directly usable version.

Follow-up: shared drives, inherited access, group/domain grants, and supported organizational identity mapping. Do not infer effective membership from an email domain alone.

## Microsoft OneDrive

Initial scope: personal OneDrive with delegated Microsoft Graph OAuth. Use stable drive/item identity, delta links, pagination, ETags, and explicit folder selection. Handle moved items, remote items, deleted facets, and expired delta tokens. Graph download URLs are short-lived and must not be logged or used as durable citations.

Follow-up: Microsoft 365 work/school accounts, Entra identity mapping, organizational sharing, and group grants. SharePoint document libraries remain separate explicitly tested scope.

## OAuth and source authorization

Use maintained OAuth libraries, state validation, PKCE where supported, exact callback allowlists, encrypted token storage, refresh concurrency control, and least-privilege read scopes. Keep client secrets server-side. Document provider app registration, test-user restrictions, consent, verification, and redirect configuration.

The connector owner's ability to fetch a file does not establish a member's right to read it. Initial owner-only connected content is visible only to its verified owner. Shared company retrieval requires tested ACL and identity mapping or a live delegated access check. Unsupported permission semantics exclude the file from shared retrieval.

## Sync correctness

Commit cursors only after all discovered events are durably recorded. Handle duplicate and out-of-order events. On invalid cursor, perform a checkpointed reconciliation; do not delete unseen records until a full authoritative scope scan succeeds. Permission updates run at higher priority than bulk content work. Define a maximum authorization staleness and block shared access when exceeded.

Disconnect must immediately remove retrieval eligibility, revoke tokens when possible, and initiate configured data cleanup. Reconnect does not create duplicate source identities.

## Acceptance

Contract fixtures and opt-in live tests cover initial listing, native export, incremental edits, moves, deletion, revocation, token expiration, rate limiting, invalid cursor, partial scan, and selected-folder scope changes. Publish a tested provider/account capability matrix.
