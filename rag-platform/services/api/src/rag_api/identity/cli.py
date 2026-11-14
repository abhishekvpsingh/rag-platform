"""Local-only operator entry point; passwords are read from the terminal, never arguments."""

import base64
import getpass
import json
import os
from collections.abc import Mapping
from urllib.parse import urlsplit

from rag_api.identity.crypto import CredentialCipher
from rag_api.identity.service import AccessDenied, IdentityService, database_engine


def configured_service(env: Mapping[str, str]) -> IdentityService:
    try:
        keys = json.loads(env["RAG_CREDENTIAL_KEYS"])
        cipher = CredentialCipher(
            {key: base64.b64decode(value, validate=True) for key, value in keys.items()},
            env["RAG_ACTIVE_CREDENTIAL_KEY"],
        )
        return IdentityService(database_engine(env["RAG_DATABASE_URL"]), cipher)
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ValueError("Invalid identity configuration") from None


def configured_origin(env: Mapping[str, str]) -> str:
    origin = env.get("RAG_AUTH_ORIGIN", "")
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("RAG_AUTH_ORIGIN must be an HTTPS origin")
    return origin


def main() -> int:
    try:
        service = configured_service(os.environ)
        email = input("Owner email: ")
        password = getpass.getpass("Owner password (12–256 characters): ")
        if password != getpass.getpass("Confirm password: "):
            print("Passwords do not match")
            return 1
        service.bootstrap(email, password)
    except (ValueError, AccessDenied):
        print("Owner setup denied; check configuration or existing bootstrap state")
        return 1
    print("Owner created. Bootstrap is now permanently disabled in this database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
