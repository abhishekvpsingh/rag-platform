import type { ReactNode } from "react";

export type ViewState =
  | "empty"
  | "loading"
  | "partial"
  | "stale"
  | "forbidden"
  | "failed"
  | "retrying"
  | "success";

const labels: Record<ViewState, string> = {
  empty: "Not available yet",
  loading: "Loading",
  partial: "Incomplete coverage",
  stale: "Needs refresh",
  forbidden: "Access unavailable",
  failed: "Unable to load",
  retrying: "Retrying",
  success: "Ready",
};

export function StatePanel({
  state,
  title,
  children,
}: {
  state: ViewState;
  title: string;
  children: ReactNode;
}) {
  return (
    <section
      className={`state-panel state-${state}`}
      aria-label={title}
      role={
        state === "failed"
          ? "alert"
          : state === "loading" || state === "retrying"
            ? "status"
            : undefined
      }
      aria-busy={state === "loading" || state === "retrying" ? true : undefined}
    >
      <span className="state-label">{labels[state]}</span>
      <h2>{title}</h2>
      <div className="state-copy">{children}</div>
    </section>
  );
}
