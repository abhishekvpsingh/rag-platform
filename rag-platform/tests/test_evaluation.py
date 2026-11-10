"""Exercise scoring failures independently of the fixture reference retriever."""

import csv
import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from rag_api.evaluation import Case, Cases, Citation, Document, evaluate, load

ROOT = Path(__file__).parent / "fixtures" / "evaluation"


def test_frozen_baseline_is_deterministic_and_splits_are_disjoint() -> None:
    splits = []
    for split in ("tuning", "heldout"):
        corpus, cases, digest = load(ROOT, split)
        report = evaluate(corpus, cases)
        assert report == evaluate(corpus, cases)
        assert report["recall_at_k"] == 1.0
        assert report["forbidden_evidence_count"] == report["invalid_citation_count"] == 0
        assert len(digest) == 64
        assert load(ROOT, split)[2] == digest
        splits.append({case.id for case in cases.cases})
    assert not splits[0] & splits[1]


@pytest.mark.parametrize(
    "document_id", ["private", "other-tenant", "stale", "unknown", "revoked", "deleted", "corrupt"]
)
def test_scorer_detects_access_leaks_even_if_case_does_not_list_them(document_id: str) -> None:
    corpus, cases, _ = load(ROOT, "tuning")
    case = next(case for case in cases.cases if case.id == "current-leave")
    assert document_id not in case.forbidden
    document = next(d for d in corpus.documents if d.id == document_id)

    def faulty_adapter(case: Case, documents: tuple[Document, ...], k: int) -> list[Citation]:
        return [
            Citation(document_id=document.id, revision=document.revision, locator=document.locator)
        ]

    report = evaluate(corpus, Cases(version=1, cases=(case,)), faulty_adapter)
    assert report["forbidden_evidence_count"] == 1
    assert report["recall_at_k"] == 0


@pytest.mark.parametrize("fault", ["unknown", "revision", "locator", "duplicate", "over_limit"])
def test_malformed_citations_cannot_inflate_recall(fault: str) -> None:
    corpus, cases, _ = load(ROOT, "tuning")
    case = next(case for case in cases.cases if case.id == "identifier")
    hit = Citation(document_id="exact-code", revision="revision-1", locator="section:1")
    outputs = {
        "unknown": [hit.model_copy(update={"document_id": "does-not-exist"})],
        "revision": [hit.model_copy(update={"revision": "old-revision"})],
        "locator": [hit.model_copy(update={"locator": "page:999"})],
        "duplicate": [hit, hit],
        "over_limit": [hit] * 4,
    }

    def faulty_adapter(case: Case, documents: tuple[Document, ...], k: int) -> list[Citation]:
        return outputs[fault]

    report = evaluate(corpus, Cases(version=1, cases=(case,)), faulty_adapter)
    assert report["invalid_citation_count"] != 0
    if fault in ("unknown", "revision", "locator"):
        assert report["recall_at_k"] == 0


def test_explicit_forbidden_evidence_is_caught_even_when_grant_is_valid() -> None:
    corpus, cases, _ = load(ROOT, "tuning")
    case = next(case for case in cases.cases if case.id == "current-leave")

    def future_adapter(case: Case, documents: tuple[Document, ...], k: int) -> list[Citation]:
        return [Citation(document_id="leave-future", revision="revision-1", locator="section:1")]

    assert (
        evaluate(corpus, Cases(version=1, cases=(case,)), future_adapter)[
            "forbidden_evidence_count"
        ]
        == 1
    )


@pytest.mark.parametrize("fault", ["unknown", "overlap", "unauthorized", "duplicate"])
def test_bad_dataset_references_fail_before_evaluation(tmp_path: Path, fault: str) -> None:
    corpus = (ROOT / "corpus.json").read_bytes()
    cases = json.loads((ROOT / "tuning.json").read_text())
    case = cases["cases"][0]
    if fault == "unknown":
        case["expected"] = ["missing"]
    elif fault == "overlap":
        case["forbidden"] = case["expected"]
    elif fault == "unauthorized":
        case["expected"] = ["private"]
    else:
        case["expected"] *= 2
    (tmp_path / "corpus.json").write_bytes(corpus)
    (tmp_path / "tuning.json").write_text(json.dumps(cases))
    with pytest.raises(ValueError):
        load(tmp_path, "tuning")


def test_unknown_schema_fields_are_rejected() -> None:
    case = json.loads((ROOT / "tuning.json").read_text())["cases"][0]
    with pytest.raises(ValidationError):
        Case.model_validate({**case, "unreviewed_option": True})


def test_numerical_expectation_matches_versioned_csv() -> None:
    _, cases, _ = load(ROOT, "tuning")
    case = next(case for case in cases.cases if case.id == "table-total")
    with (ROOT / "travel.csv").open(newline="") as source:
        rows = list(csv.DictReader(source))
    assert {row["currency"] for row in rows} == {"USD"}
    total = sum(Decimal(row["amount_usd"]) for row in rows)
    assert total == Decimal(str(case.expected_value))


def test_artifact_bytes_are_hashed_and_paths_cannot_escape(tmp_path: Path) -> None:
    for name in ("corpus.json", "tuning.json", "travel.csv"):
        (tmp_path / name).write_bytes((ROOT / name).read_bytes())
    original = load(tmp_path, "tuning")[2]
    (tmp_path / "travel.csv").write_bytes((ROOT / "travel.csv").read_bytes() + b"\n")
    assert load(tmp_path, "tuning")[2] != original
    corpus = json.loads((tmp_path / "corpus.json").read_text())
    corpus["artifacts"] = ["../outside.csv"]
    (tmp_path / "corpus.json").write_text(json.dumps(corpus))
    with pytest.raises(ValueError, match="inside the dataset"):
        load(tmp_path, "tuning")
