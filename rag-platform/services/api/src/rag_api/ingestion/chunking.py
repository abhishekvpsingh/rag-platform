"""Deterministic section-preserving UTF-8 byte bounded passages.

For byte-based tokenizers the byte limit is a conservative token upper bound.
Provider adapters additionally enforce their configured input/batch limits.
"""

import hashlib

from pydantic import BaseModel, ConfigDict

from rag_api.ingestion.parsing import Parsed, ParseFailure

CHUNKER_VERSION = "utf8-structure-v1"


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    text: str
    locator: str
    section: str
    parent: str
    start: int
    end: int


def chunks(parsed: Parsed, max_bytes: int = 2048, overlap_chars: int = 64) -> list[Chunk]:
    if not 256 <= max_bytes <= 8192 or not 0 <= overlap_chars <= 64:
        raise ValueError("Invalid chunk limits")
    result = []
    for block in parsed.blocks:
        parent = hashlib.sha256((block.locator + "\0" + block.text).encode()).hexdigest()
        start = 0
        while start < len(block.text):
            end = start
            size = 0
            while end < len(block.text):
                width = len(block.text[end].encode())
                if size + width > max_bytes:
                    break
                size += width
                end += 1
            text = block.text[start:end]
            identity = hashlib.sha256(
                f"{parent}/{start}/{end}/{CHUNKER_VERSION}".encode()
            ).hexdigest()
            result.append(
                Chunk(
                    id=identity,
                    text=text,
                    locator=block.locator,
                    section=block.section,
                    parent=parent,
                    start=start,
                    end=end,
                )
            )
            if len(result) > 20000:
                raise ParseFailure("chunk_limit")
            if end == len(block.text):
                break
            start = max(start + 1, end - overlap_chars)
    return result
