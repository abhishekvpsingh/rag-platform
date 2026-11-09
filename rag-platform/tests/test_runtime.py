"""Synthetic configuration fixtures; no accounts, external requests, or real secrets."""

import secrets
from urllib.parse import urlsplit, urlunsplit

import pytest
from rag_api.runtime import RuntimeConfigurationError, RuntimeSettings, main


@pytest.fixture
def runtime_env() -> dict[str, str]:
    def endpoint(scheme: str, host: str) -> str:
        credentials = "fixture:" + secrets.token_urlsafe(24)
        return urlunsplit((scheme, f"{credentials}@{host}", "/rag", "", ""))

    return {
        "RAG_DATABASE_URL": endpoint("postgresql", "postgres:5432"),
        "RAG_BROKER_URL": endpoint("amqp", "rabbitmq:5672"),
        "RAG_SEARCH_URL": "https://opensearch:9200",
        "RAG_SEARCH_USERNAME": "fixture-admin",
        "RAG_SEARCH_PASSWORD": secrets.token_urlsafe(24),
        "RAG_ARTIFACT_ROOT": "/var/lib/rag/artifacts",
    }


def test_config_is_explicit_and_does_not_modify_environment(runtime_env: dict[str, str]) -> None:
    original = runtime_env.copy()
    config = RuntimeSettings.from_env(runtime_env)
    assert runtime_env == original
    assert config.database_url.get_secret_value() == original["RAG_DATABASE_URL"]
    assert config.artifact_root.is_absolute()
    assert config.probe_timeout_seconds == 2
    for field in (
        "RAG_DATABASE_URL",
        "RAG_BROKER_URL",
        "RAG_SEARCH_PASSWORD",
        "RAG_SEARCH_USERNAME",
    ):
        assert original[field] not in repr(config)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("RAG_DATABASE_URL", "sqlite:///local.db"),
        ("RAG_DATABASE_URL", "postgresql://postgres/rag"),
        ("RAG_DATABASE_URL", "{database_no_name}"),
        ("RAG_DATABASE_URL", "{database_bad_host}"),
        ("RAG_DATABASE_URL", "{database_bad_port}"),
        ("RAG_DATABASE_URL", "{database}?password=leak"),
        ("RAG_BROKER_URL", "redis://redis/jobs"),
        ("RAG_SEARCH_URL", "{authenticated_search}"),
        ("RAG_SEARCH_URL", "https://opensearch:9200/private-path"),
        ("RAG_SEARCH_PASSWORD", ""),
        ("RAG_ARTIFACT_ROOT", "relative/artifacts"),
        ("RAG_ARTIFACT_ROOT", "/"),
        ("RAG_ARTIFACT_ROOT", "/var/../etc"),
        ("RAG_PROBE_TIMEOUT_SECONDS", "nan"),
        ("RAG_PROBE_TIMEOUT_SECONDS", "inf"),
        ("RAG_PROBE_TIMEOUT_SECONDS", "60"),
        ("RAG_WORKER_CONCURRENCY", "0"),
        ("RAG_WORKER_CONCURRENCY", "1.5"),
        ("RAG_API_PORT", "-1"),
        ("RAG_WEB_PORT", "8000"),
        ("RAG_BIND_HOST", "0.0.0.0"),
    ],
)
def test_invalid_config_is_rejected_without_echoing_input(
    runtime_env: dict[str, str], field: str, value: str
) -> None:
    original = runtime_env.copy()
    database = original["RAG_DATABASE_URL"]
    # Build malformed URLs with ephemeral credentials rather than hardcoding secrets.
    value = value.format(
        database=database,
        database_no_name=database.removesuffix("rag"),
        database_bad_host=database.replace("postgres:", "post\ngres:"),
        database_bad_port=database.replace(":5432", ":invalid"),
        authenticated_search=database.replace("postgresql:", "https:"),
    )
    runtime_env[field] = value
    with pytest.raises(RuntimeConfigurationError) as caught:
        RuntimeSettings.from_env(runtime_env)
    assert field in caught.value.fields
    for key in ("RAG_DATABASE_URL", "RAG_BROKER_URL", "RAG_SEARCH_PASSWORD"):
        assert original[key] not in str(caught.value)
    password = urlsplit(database).password
    assert password is not None
    assert password not in str(caught.value)
    assert "leak" not in str(caught.value)
    assert str(caught.value).startswith("Invalid or missing runtime settings: RAG_")


def test_missing_settings_are_reported_together() -> None:
    with pytest.raises(RuntimeConfigurationError) as caught:
        RuntimeSettings.from_env({})
    assert {"RAG_DATABASE_URL", "RAG_BROKER_URL", "RAG_SEARCH_PASSWORD"} <= set(caught.value.fields)


def test_cli_exit_status_and_output_are_safe(
    runtime_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for key, value in runtime_env.items():
        monkeypatch.setenv(key, value)
    assert main() == 0
    assert "services have not been probed" in capsys.readouterr().out
    monkeypatch.setenv(
        "RAG_DATABASE_URL", runtime_env["RAG_DATABASE_URL"].replace(":5432", ":invalid")
    )
    assert main() == 1
    output = capsys.readouterr().out
    assert "RAG_DATABASE_URL" in output
    password = urlsplit(runtime_env["RAG_DATABASE_URL"]).password
    assert password is not None
    assert password not in output
