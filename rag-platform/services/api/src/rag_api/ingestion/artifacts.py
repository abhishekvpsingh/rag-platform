"""Immutable tenant-scoped file storage; authorization belongs to the repository."""

import hashlib
import os
import re
import tempfile
from pathlib import Path

from rag_api.ingestion.parsing import MAX_FILE


class LocalArtifacts:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def path(self, tenant: str, key: str) -> Path:
        if not re.fullmatch(r"[a-f0-9-]{36}", tenant) or not re.fullmatch(r"[a-f0-9]{64}", key):
            raise ValueError("Invalid artifact identifier")
        directory = self.root / tenant
        directory.mkdir(mode=0o700, exist_ok=True)
        if directory.is_symlink() or directory.resolve().parent != self.root:
            raise ValueError("Unsafe artifact directory")
        return directory / key

    def put(self, tenant: str, data: bytes) -> str:
        if not data or len(data) > MAX_FILE:
            raise ValueError("Artifact size limit")
        key = hashlib.sha256(data).hexdigest()
        path = self.path(tenant, key)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
            tmp = Path(output.name)
            try:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
                try:
                    os.link(tmp, path)
                except FileExistsError:
                    if self.read(tenant, key) != data:
                        raise ValueError("Artifact integrity failure") from None
            finally:
                tmp.unlink(missing_ok=True)
        return key

    def read(self, tenant: str, key: str) -> bytes:
        path = self.path(tenant, key)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as input_file:
            data = input_file.read(MAX_FILE + 1)
        if len(data) > MAX_FILE or hashlib.sha256(data).hexdigest() != key:
            raise ValueError("Artifact integrity failure")
        return data
