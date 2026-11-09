"""Synthetic configuration fixtures; no accounts, external requests, or real secrets."""

import pytest
from rag_api.runtime import RuntimeConfigurationError, RuntimeSettings, main


@pytest.fixture
def runtime_env() -> dict[str, str]:
    return {
        "RAG_DATABASE_URL": "postgresql://fixture:synthetic-db@postgres:5432/rag",
        "RAG_BROKER_URL": "amqp://fixture:synthetic-broker@rabbitmq:5672/rag",
        "RAG_SEARCH_URL": "https://opensearch:9200",
        "RAG_SEARCH_USERNAME": "fixture-admin",
        "RAG_SEARCH_PASSWORD": "synthetic-search",
        "RAG_ARTIFACT_ROOT": "/var/lib/rag/artifacts",
    }


def test_config_is_explicit_and_does_not_modify_environment(runtime_env: dict[str, str]) -> None:
    original = runtime_env.copy()
    config = RuntimeSettings.from_env(runtime_env)
    assert runtime_env == original
    assert config.database_url.get_secret_value() == original["RAG_DATABASE_URL"]
    assert config.artifact_root.is_absolute()
    assert config.probe_timeout_seconds == 2
    for value in ("synthetic-db", "synthetic-broker", "synthetic-search", "fixture-admin"):
        assert value not in repr(config)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("RAG_DATABASE_URL", "sqlite:///local.db"),
        ("RAG_DATABASE_URL", "postgresql://postgres/rag"),
        ("RAG_DATABASE_URL", "postgresql://user:private-value@postgres/"),
        ("RAG_DATABASE_URL", "postgresql://user:private-value@post\ngres/rag"),
        ("RAG_DATABASE_URL", "postgresql://user:private-value@postgres:invalid/rag"),
        ("RAG_DATABASE_URL", "postgresql://user:private-value@postgres/rag?password=leak"),
        ("RAG_BROKER_URL", "redis://user:private-value@redis/jobs"),
        ("RAG_SEARCH_URL", "https://user:private-value@opensearch:9200"),
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
    runtime_env[field] = value
    with pytest.raises(RuntimeConfigurationError) as caught:
        RuntimeSettings.from_env(runtime_env)
    assert field in caught.value.fields
    assert "private-value" not in str(caught.value)
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
    monkeypatch.setenv("RAG_DATABASE_URL", "https://user:private-value@invalid/rag")
    assert main() == 1
    output = capsys.readouterr().out
    assert "RAG_DATABASE_URL" in output
    assert "private-value" not in output
