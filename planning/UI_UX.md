# Web experience and design system

## Direction

A calm, polished enterprise workspace with a clear sidebar, spacious content, crisp typography, restrained color, and purposeful diagrams. Use a deep navy/neutral foundation with teal accents, subtle gradients for onboarding illustrations, and accessible status colors. Avoid decorative graphics that obscure evidence or operational state.

Create shared tokens for color, spacing, type, radii, elevation, focus, and motion. Use accessible primitives and a consistent component library. Target WCAG 2.2 AA, keyboard navigation, screen-reader labels, reduced motion, and responsive tablet/mobile layouts.

## Navigation and screens

- Ask: searchable conversations, scope/date controls, streamed status, concise answer, claim-linked citations, evidence drawer, source preview, historical comparison, feedback.
- Sources: provider cards, account type support, OAuth connection, folder selection, sync summary, file status, errors/retry, permission freshness, disconnect.
- Knowledge: authorized documents, revisions, policy metadata, conflicts/review queue, graph exploration only when enabled.
- Quality: dataset/run comparison, retrieval and citation metrics, failures and limitations.
- Operations: queue/worker health, freshness, costs, capacity trends, recommendations.
- Settings: models, ingestion, identity/security, policy rules, retention, graph, infrastructure, budgets, recommendation controls.

## Onboarding

Bootstrap owner → select available deployment profile → configure models and data-transmission policy → connect supported source account → select folders → inspect limits/estimate → start ingestion → ask a grounded question. Explain real prerequisites and offer actionable errors. Credentials remain server-side.

## Required states

For every data screen specify loading, empty, partial, stale, forbidden, failed, retrying, and success states. Show incomplete corpus coverage and last successful sync. Do not reveal inaccessible titles in previews or error messages. Surface uncertainty and conflicting policies without hiding them in tooltips.

## Settings and upgrades

Use basic controls with advanced sections. Explain whether a change requires restart, reindex, migration, more cost, or external data transmission. Validate before saving. Secret fields are write-only with masked connection status.

Graph and distributed mode are off by default. A recommendation card shows evidence, expected benefit, uncertainty, estimate, prerequisites, trial/migration steps, and dismiss/snooze controls. Never imply machines exist merely because a capacity setting was saved.

## Verification

Browser checks cover onboarding, OAuth callback errors, ingestion progress, answer/citation access, policy conflict, revoked access, settings validation, and upgrade previews. Test narrow and wide viewports and keyboard flows. Use synthetic fixtures for screenshots; label demonstration data clearly.

## T005 shell implementation

The shell provides seven routes including Overview and Quality, persistent
keyboard-accessible navigation, active-page labels, a skip link, responsive
layout and shared color/spacing/type/focus/motion tokens. StatePanel defines
loading, empty, partial, stale, forbidden, failed, retrying and success
presentation; current data screens show honest unavailable states. Next loading
and error boundaries provide status announcements and a real route retry.
No authenticated data or configuration form is connected yet. Browser checks
cover every route, desktop/mobile overflow, keyboard navigation and 404 recovery;
full WCAG audit and data-flow tests remain later acceptance work.
