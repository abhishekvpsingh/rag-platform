"""Worker control round trip, without printing connection errors or credentials."""


def main() -> int:
    try:
        from rag_api.worker import app

        replies = app.control.inspect(timeout=3, destination=["runtime@worker"]).ping()
        return 0 if replies and replies.get("runtime@worker", {}).get("ok") == "pong" else 1
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
