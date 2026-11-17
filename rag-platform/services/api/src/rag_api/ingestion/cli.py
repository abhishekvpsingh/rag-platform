"""Submit an existing authorized source revision from a local file; no source proof bypass."""

import argparse
import getpass
import os
from pathlib import Path

from rag_api.identity.cli import configured_service
from rag_api.ingestion.artifacts import LocalArtifacts
from rag_api.ingestion.parsing import MAX_FILE
from rag_api.ingestion.runtime import configured_embedder
from rag_api.ingestion.service import IngestionService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--connection", required=True)
    parser.add_argument("--source-key", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument(
        "--format", required=True, choices=["txt", "md", "html", "csv", "pdf", "docx", "xlsx"]
    )
    args = parser.parse_args()
    identity = None
    try:
        identity = configured_service(os.environ)
        model = configured_embedder()
        token = getpass.getpass("Existing session token: ")
        with args.file.open("rb") as source:
            content = source.read(MAX_FILE + 1)
        service = IngestionService(identity, LocalArtifacts(Path(os.environ["RAG_ARTIFACT_ROOT"])))
        job = service.submit(
            token,
            args.connection,
            args.source_key,
            args.source_version,
            args.format,
            content,
            model.config,
        )
        print(f"Job {job.id}: {job.state}")
        return 0
    except Exception:
        print(
            "Submission denied or unavailable; check source authorization, file and configuration"
        )
        return 1
    finally:
        if identity is not None:
            identity.engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
