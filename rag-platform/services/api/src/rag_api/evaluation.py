"""Offline fixture baseline and scoring, not production retrieval/authorization."""

import argparse
import hashlib
import json
import math
import os
import platform
import re
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class FixtureModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_min_length=1, allow_inf_nan=False)


class Document(FixtureModel):
    id: str
    revision: str
    locator: str
    tenant: str
    owner: str
    readers: tuple[str, ...] = ()
    permissions: Literal["fresh", "stale", "unknown", "revoked"] = "fresh"
    deleted: bool = False
    parse_status: Literal["valid", "corrupt"] = "valid"
    effective_from: date | None = None
    effective_until: date | None = None
    region: str | None = None
    text: str

    @model_validator(mode="after")
    def valid_interval(self) -> "Document":
        if self.effective_from and self.effective_until:
            if self.effective_until <= self.effective_from:
                raise ValueError("Effective interval must be nonempty")
        return self


class Case(FixtureModel):
    id: str
    tenant: str
    actor: str
    as_of: date
    region: str | None = None
    query: str
    expected: tuple[str, ...]
    forbidden: tuple[str, ...]
    behavior: Literal["answer", "abstain", "conflict", "analytical"]
    expected_value: float | None = None

    @model_validator(mode="after")
    def behavior_expectations(self) -> "Case":
        if self.behavior == "analytical" and self.expected_value is None:
            raise ValueError("Analytical cases require an expected numeric value")
        if self.behavior != "abstain" and not self.expected:
            raise ValueError("Answer/conflict/analytical cases require expected evidence")
        return self


class Corpus(FixtureModel):
    version: Literal[1]
    processing_version: str
    artifacts: tuple[str, ...] = ()
    documents: tuple[Document, ...]


class Cases(FixtureModel):
    version: Literal[1]
    cases: tuple[Case, ...]


class Citation(FixtureModel):
    document_id: str
    revision: str
    locator: str


def authorized(document: Document, case: Case) -> bool:
    """Synthetic grant oracle; production source ACL support requires its own tests."""
    return (
        document.tenant == case.tenant
        and (document.owner == case.actor or case.actor in document.readers)
        and document.permissions == "fresh"
        and not document.deleted
        and document.parse_status == "valid"
    )


def applicable(document: Document, case: Case) -> bool:
    return (
        (document.effective_from is None or document.effective_from <= case.as_of)
        and (document.effective_until is None or case.as_of < document.effective_until)
        and (document.region is None or document.region == case.region)
    )


def tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold()))


def lexical_baseline(case: Case, documents: tuple[Document, ...], k: int) -> list[Citation]:
    """Token overlap with fixture-only grants/date filters; no models or network."""
    query = tokens(case.query)
    candidates = []
    for document in documents:
        if authorized(document, case) and applicable(document, case):
            score = len(query & tokens(document.text))
            if score:
                candidates.append((-score, document.id, document))
    return [
        Citation(document_id=d.id, revision=d.revision, locator=d.locator)
        for _, _, d in sorted(candidates)[:k]
    ]


def load(root: Path, split: str) -> tuple[Corpus, Cases, str]:
    if split not in ("tuning", "heldout"):
        raise ValueError("Unknown dataset split")
    corpus_bytes = (root / "corpus.json").read_bytes()
    case_bytes = (root / f"{split}.json").read_bytes()
    corpus = Corpus.model_validate_json(corpus_bytes)
    cases = Cases.model_validate_json(case_bytes)
    ids = {d.id for d in corpus.documents}
    if len(ids) != len(corpus.documents) or not ids or not cases.cases:
        raise ValueError("Corpus must have unique documents and nonempty cases")
    case_ids = [case.id for case in cases.cases]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Duplicate case ID")
    for case in cases.cases:
        if len(set(case.expected)) != len(case.expected):
            raise ValueError("Duplicate expected evidence")
        if set(case.expected) & set(case.forbidden):
            raise ValueError("Expected evidence cannot also be forbidden")
        if not (set(case.expected) | set(case.forbidden)) <= ids:
            raise ValueError("Case references missing documents")
        if any(
            not authorized(d, case) or not applicable(d, case)
            for d in corpus.documents
            if d.id in case.expected
        ):
            raise ValueError("Expected evidence violates fixture grants/applicability")
    content = corpus_bytes + b"\0" + case_bytes
    for name in sorted(corpus.artifacts):
        path = root / name
        if Path(name).name != name or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Fixture artifact must stay inside the dataset directory")
        content += b"\0" + name.encode() + b"\0" + path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    return corpus, cases, digest


Retriever = Callable[[Case, tuple[Document, ...], int], list[Citation]]


def evaluate(
    corpus: Corpus, cases: Cases, retriever: Retriever = lexical_baseline, k: int = 3
) -> dict[str, object]:
    """Score adapter output as received; never hide leaks by post-filtering results."""
    if not 1 <= k <= 100:
        raise ValueError("k must be between 1 and 100")
    documents = {d.id: d for d in corpus.documents}
    rows = []
    recalls: list[float] = []
    leaks = invalid = 0
    for case in cases.cases:
        hits = retriever(case, corpus.documents, k)
        seen: set[str] = set()
        valid_ids = []
        for hit in hits:
            document = documents.get(hit.document_id)
            if document is None or hit.document_id in seen:
                invalid += 1
                continue
            seen.add(hit.document_id)
            if hit.document_id in case.forbidden or not authorized(document, case):
                leaks += 1
            if hit.revision != document.revision or hit.locator != document.locator:
                invalid += 1
                continue
            valid_ids.append(hit.document_id)
        if len(hits) > k:
            invalid += 1
        found = len(set(valid_ids[:k]) & set(case.expected))
        recall = found / len(case.expected) if case.expected else None
        if recall is not None:
            recalls.append(recall)
        rows.append({"id": case.id, "returned": valid_ids, "recall_at_k": recall})
    return {
        "k": k,
        "case_count": len(cases.cases),
        "recall_at_k": sum(recalls) / len(recalls) if recalls else None,
        "forbidden_evidence_count": leaks,
        "invalid_citation_count": invalid,
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures/evaluation"))
    parser.add_argument("--split", choices=("tuning", "heldout"), default="heldout")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    corpus, cases, digest = load(args.fixtures, args.split)
    report = evaluate(corpus, cases)
    report.update(
        dataset_sha256=digest,
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        split=args.split,
        baseline_version="lexical-fixture-v1",
        processing_version=corpus.processing_version,
        model_version="none",
        index_version="none",
        prompt_version="none",
    )
    if args.benchmark:
        samples = []
        for _ in range(100):
            start = time.perf_counter()
            evaluate(corpus, cases)
            samples.append((time.perf_counter() - start) * 1000)
        report["benchmark"] = {
            "unit": "ms per full split, warm in-memory, serial",
            "samples": len(samples),
            "concurrency": 1,
            "machine": platform.machine(),
            "logical_cpus": os.cpu_count(),
            "python_version": platform.python_version(),
            "p50": sorted(samples)[math.ceil(len(samples) * 0.5) - 1],
            "p95": sorted(samples)[math.ceil(len(samples) * 0.95) - 1],
        }
    recall = report["recall_at_k"]
    report["quality_target_met"] = (
        isinstance(recall, float)
        and recall >= 0.9
        and report["forbidden_evidence_count"] == 0
        and report["invalid_citation_count"] == 0
    )
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["quality_target_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
