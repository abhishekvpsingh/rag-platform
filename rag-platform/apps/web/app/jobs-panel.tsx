"use client";

import { useEffect, useState } from "react";
import { StatePanel } from "./state-panel";

type Job = {
  id: string;
  kind: string;
  state: string;
  attempts: number;
  progress: number;
};
type View = {
  state: "loading" | "ready" | "forbidden" | "failed";
  jobs: Job[];
};

export function JobsPanel() {
  const [view, setView] = useState<View>({ state: "loading", jobs: [] });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const response = await fetch("/api/jobs", {
          cache: "no-store",
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        if (response.status === 401 || response.status === 403) {
          setView({ state: "forbidden", jobs: [] });
          return;
        }
        if (!response.ok) throw new Error("Unavailable");
        const jobs: Job[] = await response.json();
        if (controller.signal.aborted) return;
        setView({ state: "ready", jobs });
        timer = setTimeout(refresh, 5000);
      } catch {
        if (!controller.signal.aborted) setView({ state: "failed", jobs: [] });
      }
    }
    void refresh();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [revision]);

  if (view.state === "loading")
    return (
      <StatePanel state="loading" title="Loading jobs">
        <p>Checking your background work.</p>
      </StatePanel>
    );
  if (view.state === "forbidden")
    return (
      <StatePanel state="forbidden" title="Sign in to view your jobs">
        <p>
          An authenticated HTTPS session is required. Jobs are private to their
          owner; sign-in forms are not available in this preview.
        </p>
      </StatePanel>
    );
  if (view.state === "failed")
    return (
      <StatePanel state="failed" title="Jobs could not be refreshed">
        <p>Job status is unavailable. No previous job details are displayed.</p>
        <button
          className="primary-link"
          onClick={() => {
            setView({ state: "loading", jobs: [] });
            setRevision((value) => value + 1);
          }}
        >
          Refresh jobs
        </button>
      </StatePanel>
    );
  return (
    <section className="state-panel" aria-label="Background jobs">
      <span className="state-label">Live job status</span>
      <h2>Background jobs</h2>
      <p>
        Latest 50 jobs owned by your account. Updates every five seconds. Worker
        checks verify background execution; they do not ingest documents.
      </p>
      {view.jobs.length === 0 ? (
        <p>No background jobs yet.</p>
      ) : (
        <ul className="job-list">
          {view.jobs.map((job) => (
            <li key={job.id}>
              <strong>Worker check</strong>
              <span className="state-label">{job.state}</span>
              <p>
                Attempt {job.attempts} · {job.progress}% complete
              </p>
              <progress
                value={job.progress}
                max={100}
                aria-label={`Worker check ${job.id} progress`}
              />
              <small>Job {job.id}</small>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
