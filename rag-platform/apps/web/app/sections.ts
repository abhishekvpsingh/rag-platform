export const sections = {
  ask: {
    title: "Ask with evidence",
    description:
      "Find a grounded answer, understand what applies, and follow every source.",
    emptyTitle: "Your first answer starts with a source",
    emptyText:
      "Question answering is not available yet. Once a supported source is connected and indexed, this space will hold your conversations and cited answers.",
    nextHref: "/sources",
    nextLabel: "View source availability",
    cards: [
      {
        title: "Choose the right scope",
        text: "Future questions will use only sources you are authorized to access, with current or historical context.",
      },
      {
        title: "Follow the evidence",
        text: "Answers will include inspectable citations. Missing or conflicting evidence will be made explicit.",
      },
    ],
  },
  sources: {
    title: "Sources",
    description:
      "Connect knowledge while keeping ownership and source permissions explicit.",
    emptyTitle: "Source connections are not available yet",
    emptyText:
      "No storage accounts can be connected through this preview. OAuth, folder selection and sync controls will appear once the supported connectors are verified.",
    nextHref: "/knowledge",
    nextLabel: "Explore the knowledge workspace",
    cards: [
      {
        title: "Google Drive · My Drive",
        text: "Planned. Personal file discovery, changes, deletions and permission checks require connector validation.",
      },
      {
        title: "Personal OneDrive",
        text: "Planned. Work and school accounts are outside the initial connector scope.",
      },
    ],
  },
  knowledge: {
    title: "Knowledge",
    description:
      "Understand your documents, their history, and which policies apply.",
    emptyTitle: "The document library is not available yet",
    emptyText:
      "No document data is loaded in this preview. Ingestion and permission-aware document browsing are still being built; there are no sample company files here.",
    nextHref: "/sources",
    nextLabel: "View source availability",
    cards: [
      {
        title: "Preserve history",
        text: "The library will keep source revisions and evidence locations so changes stay traceable.",
      },
      {
        title: "Resolve applicability",
        text: "Effective dates, scope and conflicting policies will be reviewed with supporting evidence. Graph features remain off.",
      },
    ],
  },
  quality: {
    title: "Quality",
    description:
      "Evaluate retrieval, citations and access boundaries before relying on an answer.",
    emptyTitle: "Live evaluation results are not connected",
    emptyText:
      "An offline synthetic evaluation baseline exists. This screen does not load its reports or display projected product metrics.",
    nextHref: "/operations",
    nextLabel: "View operations availability",
    cards: [
      {
        title: "Grounding and citations",
        text: "Future reports will separate retrieval coverage, valid citations and unsupported claims.",
      },
      {
        title: "Access boundaries",
        text: "Permission tests must reject forbidden evidence before it reaches a model. Synthetic results are not production validation.",
      },
    ],
  },
  operations: {
    title: "Operations",
    description:
      "Understand freshness and service health without losing sight of incomplete work.",
    emptyTitle: "Operational data is not connected to this view",
    emptyText:
      "The runtime has readiness checks, but this page does not fetch them. Queue progress, freshness and usage will appear when their authenticated APIs are available.",
    nextHref: "/settings",
    nextLabel: "View workspace settings",
    cards: [
      {
        title: "Work and recovery",
        text: "Durable job progress, retry and cancellation are planned. No running jobs or health measurements are implied here.",
      },
      {
        title: "Capacity with evidence",
        text: "Distributed deployment remains off. Recommendations will require measured workloads and explicit administrator decisions.",
      },
    ],
  },
  settings: {
    title: "Settings",
    description:
      "Make deliberate choices about identity, models, data and deployment.",
    emptyTitle: "Settings controls are not connected yet",
    emptyText:
      "Owner setup and HTTPS session APIs are available through operator configuration. This preview has no login or settings forms and never asks you to enter credentials.",
    nextHref: "/",
    nextLabel: "Return to overview",
    cards: [
      {
        title: "Identity and access",
        text: "Tenant membership, expiring sessions and encrypted credential storage are implemented. Source ownership remains separate from administrator privileges.",
      },
      {
        title: "Models and data",
        text: "Provider configuration and data-transmission controls are planned. No model is called by this preview.",
      },
      {
        title: "Optional capabilities",
        text: "Graph and distributed modes remain off. Saving a setting will never imply that machines have been provisioned.",
      },
    ],
  },
} as const;

export type Section = keyof typeof sections;
export function isSection(value: string): value is Section {
  return Object.hasOwn(sections, value);
}
