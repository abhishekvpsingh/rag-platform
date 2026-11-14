"""Validated development runtime configuration; never render credential values."""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import SecretStr


class RuntimeConfigurationError(ValueError):
    """Safe to display: only configuration variable names, never their input values."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = tuple(sorted(set(fields)))
        super().__init__("Invalid or missing runtime settings: " + ", ".join(self.fields))


@dataclass(frozen=True)
class RuntimeSettings:
    """Explicit configuration for the single-machine development runtime.

    Loading is side-effect free: it neither creates directories nor contacts services.
    Secrets stay server-side. Production deployment validation belongs to its milestone.
    """

    database_url: SecretStr = field(repr=False)
    broker_url: SecretStr = field(repr=False)
    search_url: str
    search_username: SecretStr = field(repr=False)
    search_password: SecretStr = field(repr=False)
    artifact_root: Path
    probe_timeout_seconds: float
    worker_concurrency: int
    api_port: int
    web_port: int
    bind_host: str = "127.0.0.1"

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "RuntimeSettings":
        """Consume an explicit environment mapping so tests never need real secrets."""
        errors: list[str] = []

        def required(name: str) -> str:
            value = env.get(name, "")
            if not value or value != value.strip():
                errors.append(name)
            return value

        def endpoint(name: str, schemes: set[str], authenticated: bool) -> str:
            value = required(name)
            try:
                parsed = urlsplit(value)
                valid = (
                    parsed.scheme in schemes
                    and parsed.hostname
                    and parsed.port != 0
                    and not any(character.isspace() for character in value)
                    and not parsed.query
                    and not parsed.fragment
                )
                if authenticated:
                    valid = valid and bool(parsed.username and parsed.password and parsed.path)
                    if parsed.scheme == "postgresql":
                        valid = valid and parsed.path != "/"
                else:
                    valid = valid and not (parsed.username or parsed.password)
                    valid = valid and parsed.path in ("", "/")
                if not valid:
                    errors.append(name)
            except ValueError:
                errors.append(name)
            return value

        def number(name: str, default: str, minimum: float, maximum: float) -> float:
            try:
                value = float(env.get(name, default))
                if not math.isfinite(value) or not minimum <= value <= maximum:
                    raise ValueError
                return value
            except ValueError:
                errors.append(name)
                return float(default)

        def integer(name: str, default: str, minimum: int, maximum: int) -> int:
            value = number(name, default, minimum, maximum)
            if not value.is_integer():
                errors.append(name)
            return int(value)

        database = endpoint("RAG_DATABASE_URL", {"postgresql"}, authenticated=True)
        broker = endpoint("RAG_BROKER_URL", {"amqp", "amqps"}, authenticated=True)
        search = endpoint("RAG_SEARCH_URL", {"http", "https"}, authenticated=False)
        username = required("RAG_SEARCH_USERNAME")
        password = required("RAG_SEARCH_PASSWORD")
        root = Path(required("RAG_ARTIFACT_ROOT"))
        if not root.is_absolute() or ".." in root.parts or root == Path("/"):
            errors.append("RAG_ARTIFACT_ROOT")
        timeout = number("RAG_PROBE_TIMEOUT_SECONDS", "2", 0.1, 10)
        concurrency = integer("RAG_WORKER_CONCURRENCY", "1", 1, 4)
        api_port = integer("RAG_API_PORT", "8000", 1024, 65535)
        web_port = integer("RAG_WEB_PORT", "3000", 1024, 65535)
        if api_port == web_port:
            errors.extend(["RAG_API_PORT", "RAG_WEB_PORT"])
        bind_host = env.get("RAG_BIND_HOST", "127.0.0.1")
        if bind_host != "127.0.0.1":
            errors.append("RAG_BIND_HOST")
        if errors:
            raise RuntimeConfigurationError(errors)
        return cls(
            database_url=SecretStr(database),
            broker_url=SecretStr(broker),
            search_url=search,
            search_username=SecretStr(username),
            search_password=SecretStr(password),
            artifact_root=root,
            probe_timeout_seconds=timeout,
            worker_concurrency=concurrency,
            api_port=api_port,
            web_port=web_port,
            bind_host=bind_host,
        )


def main() -> int:
    """Validate current process settings without connecting or displaying secrets."""
    import os

    try:
        RuntimeSettings.from_env(os.environ)
    except RuntimeConfigurationError as error:
        print(error)
        return 1
    print("Development runtime configuration is valid; services have not been probed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
