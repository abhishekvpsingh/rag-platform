# Temporal and authoritative knowledge

## Resolution model

Latest upload, latest modification, approved policy, and policy effective today are different concepts. Determine applicability from explicit scope, status, effective interval, source authority, and reviewed supersession relationships. Preserve uncertainty where these are missing.

Date extraction must retain the evidence span and confidence. Use source metadata as a signal, not a substitute for business effective dates. Administrators configure authority by source/path/document class and review ambiguous assertions. Avoid a universal numerical score that silently resolves contradictory authoritative documents.

## Selection order

Authorize candidates; match explicit or verified user scope; select the requested as-of date (today by default in tenant timezone); exclude known drafts and inapplicable intervals; follow scoped supersession; compare applicable authorities; surface unresolved conflicts. Do not force a definitive answer when the only evidence has unknown status or dates.

A future policy is not the current policy. A reuploaded archive does not supersede an approved policy. Partial replacements may leave other sections active. Preserve document and clause-level provenance.

## Illustrative required fixtures

| Case | Expected behavior |
|---|---|
| 2025 approved policy: 20 days; 2026 approved effective policy: 24 days | Current answer uses 24 days; short optional historical note uses 20 |
| Old policy reuploaded after current policy | Still use the currently applicable approved policy |
| Approved policy effective next year | Do not apply early; mention future change only when relevant |
| UK and India policies differ | Use verified scope or ask a concise clarifying question |
| Two equally authoritative active policies conflict | Report conflict with both permitted citations |
| Question asks as of 2023 | Use 2023 effective evidence and label the historical answer |
| New policy restricted to another group | Do not leak its existence; answer only within authorized evidence and qualify certainty |
| Effective date missing | State uncertainty; route review rather than inventing a date |
| One clause superseded | Keep unaffected clauses available with accurate applicability |

## Review workflow

Queue low-confidence policy extraction, conflicts, and suggested supersession for authorized reviewers. Record reviewer, timestamp, evidence, scope, and rationale. A subsequent source change marks affected reviews stale. Review privileges do not bypass source access.

## History and retention

Keep immutable observed revisions subject to source contract, tenant retention, and deletion requirements. Historical queries do not restore deleted access. Do not promise historical answers when the relevant revision was never ingested or has been purged.
