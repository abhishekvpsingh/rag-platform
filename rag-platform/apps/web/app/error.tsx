"use client";
import { StatePanel } from "./state-panel";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <StatePanel state="failed" title="This view could not be loaded">
      <p>
        Try loading the view again. No document or account details are shown
        here.
      </p>
      <button className="primary-link" onClick={reset}>
        Try again
      </button>
    </StatePanel>
  );
}
