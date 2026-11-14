"""Run against only the named development Compose project; never delete volumes."""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compose(*args: str) -> None:
    subprocess.run(["docker", "compose", *args], cwd=ROOT, check=True)


def ready(expected: bool = True, dependency: str | None = None) -> None:
    port = os.environ.get("RAG_API_PORT", "8000")
    for _ in range(40):
        try:
            try:
                response = urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health/ready", timeout=10
                )
            except urllib.error.HTTPError as error:
                response = error
            with response:
                report = json.load(response)
            if expected and report["status"] == "ready":
                return
            if not expected and any(
                item["name"] == dependency and item["status"] == "unavailable"
                for item in report["dependencies"]
            ):
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health/live", timeout=5
                ) as live:
                    assert live.status == 200
                return
        except (OSError, ValueError):
            pass
        time.sleep(2)
    raise RuntimeError("Expected runtime health state was not reached")


def main() -> None:
    compose("up", "-d", "--wait", "--wait-timeout", "300")
    ready()
    container_ids = subprocess.check_output(
        ["docker", "compose", "ps", "-q"], cwd=ROOT, text=True
    ).split()
    containers = json.loads(subprocess.check_output(["docker", "inspect", *container_ids]))
    for container in containers:
        for port, bindings in container["HostConfig"]["PortBindings"].items():
            assert port in ("8000/tcp", "3000/tcp")
            assert all(binding["HostIp"] == "127.0.0.1" for binding in bindings)
    compose("exec", "-T", "api", "python", "scripts/runtime_smoke.py", "write")
    compose("restart")
    ready()
    compose("exec", "-T", "api", "python", "scripts/runtime_smoke.py", "read")
    compose("stop", "--timeout", "30")
    stopped_ids = subprocess.check_output(
        ["docker", "compose", "ps", "--all", "-q"], cwd=ROOT, text=True
    ).split()
    stopped = json.loads(subprocess.check_output(["docker", "inspect", *stopped_ids]))
    assert len(stopped) == 6
    assert all(not item["State"]["Running"] and not item["State"]["OOMKilled"] for item in stopped)
    exit_codes = {
        item["Config"]["Labels"]["com.docker.compose.service"]: item["State"]["ExitCode"]
        for item in stopped
    }
    assert all(code in (0, 143) for code in exit_codes.values()), exit_codes
    compose("down", "--timeout", "30")
    compose("up", "-d", "--wait", "--wait-timeout", "300")
    ready()
    compose("exec", "-T", "api", "python", "scripts/runtime_smoke.py", "read")
    for service, dependency in (
        ("postgres", "postgres"),
        ("rabbitmq", "rabbitmq"),
        ("opensearch", "opensearch"),
        ("worker", "worker"),
    ):
        compose("stop", service)
        try:
            ready(False, dependency)
        finally:
            compose("start", service)
        ready()
    print("Restart, recreation persistence, dependency failure/recovery: passed")


if __name__ == "__main__":
    main()
