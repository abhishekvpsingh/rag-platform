import { StatePanel } from "./state-panel";
export default function Loading() {
  return (
    <StatePanel state="loading" title="Loading workspace">
      <p>Please wait while this page loads.</p>
    </StatePanel>
  );
}
