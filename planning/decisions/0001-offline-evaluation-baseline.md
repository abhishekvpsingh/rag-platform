# 0001 — Versioned offline evaluation baseline

- Status: accepted (T003).
- Context: retrieval, temporal resolution, and live accounts do not exist yet.
  Quality/security expectations must precede tuning, without introducing another
  production search backend or requiring model spending.
- Decision: commit invented documents and disjoint tuning/held-out question sets
  as JSON; define executable strict Pydantic schemas alongside a deterministic
  Unicode lexical-overlap reference baseline. Encode explicit source grants,
  stale/unknown/revoked permissions, revisions, locators, applicability, expected
  answer behavior, numerical values, and forbidden evidence. Score adapter output
  independently of its filtering, including inferred grant violations and invalid
  citations. Hash exact dataset and runner bytes in reports.
- Targets: Recall@3 >= 0.90; zero forbidden/invalid citations; opt-in warm serial
  held-out split p95 <= 50 ms on the declared Mac. Targets were recorded before the
  initial run and apply only to this fixture workload. Timing is not a CI gate.
- Alternatives: live provider evaluation now would require unavailable accounts,
  cost, and nondeterministic outputs. A second search engine would prejudge T011.
  Expected answers without explicit forbidden evidence would miss access leaks.
- Compatibility: Python 3.12.14/Pydantic 2.14.3 schemas and CLI run with the T001
  frozen lockfile; Ruff, mypy, pytest and existing ASGI smoke tests verify the same
  environment. No new dependency or service is needed. Later capabilities need
  their own compatibility evidence; DuckDB/LLM compatibility is not claimed.
- Consequences: baseline scores describe the reference only. The synthetic grant
  oracle does not certify connector ACLs. Answer generation, prompt injection
  defense, SQL execution, ranking evaluation at scale, and production temporal
  resolution remain future work. Keep held-out questions out of tuning and version
  fixture changes. Do not equate a tiny corpus score with real-source quality.
- Evidence: [T003 verification](../verification/T003.md), [evaluation specification](../TESTING_AND_EVALUATION.md).
- Owner software-license selection remains pending before release. No license was
  chosen by this decision.
