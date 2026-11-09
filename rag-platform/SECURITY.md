# Security policy

## Status

There are no supported software releases yet. Do not deploy this specification-only repository as a production system or upload confidential files to unreviewed development builds.

## Reporting

Use GitHub private vulnerability reporting if the repository owner has enabled it. If unavailable, request a private reporting channel without posting exploit details, credentials, personal data, or customer documents in a public issue. A maintained private contact and release support policy must be added before the first software release.

## Development expectations

Never commit OAuth tokens, API keys, `.env` files, production datasets, or diagnostic bundles containing private data. Use synthetic fixtures. Rotate any accidentally disclosed credentials and follow the provider's incident procedures.

The [security and permission specification](../planning/SECURITY_AND_PERMISSIONS.md) defines implementation requirements; it does not certify implementation compliance.
