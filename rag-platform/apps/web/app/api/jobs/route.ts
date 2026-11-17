import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const headers = { "Cache-Control": "no-store", Vary: "Cookie" };
  const token = request.cookies.get("__Host-rag_session")?.value;
  if (!token || token.length > 128) {
    return NextResponse.json(
      { detail: "Authentication required" },
      { status: 401, headers },
    );
  }
  const configured = process.env.RAG_INTERNAL_API_URL;
  if (!configured) {
    return NextResponse.json(
      { detail: "Job service is not configured" },
      { status: 503, headers },
    );
  }
  try {
    const origin = new URL(configured);
    if (
      !["http:", "https:"].includes(origin.protocol) ||
      origin.username ||
      origin.password ||
      origin.search ||
      origin.hash ||
      origin.pathname !== "/"
    )
      throw new Error("Invalid API origin");
    const response = await fetch(new URL("/api/v1/jobs", origin), {
      headers: { Cookie: `__Host-rag_session=${encodeURIComponent(token)}` },
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) {
      const status = [401, 403].includes(response.status)
        ? response.status
        : 503;
      return NextResponse.json(
        { detail: "Job service unavailable" },
        { status, headers },
      );
    }
    const jobs: unknown = await response.json();
    if (!Array.isArray(jobs) || jobs.length > 50)
      throw new Error("Invalid job response");
    const states = [
      "queued",
      "running",
      "retrying",
      "succeeded",
      "failed",
      "cancelled",
      "superseded",
    ];
    const safe = jobs.map((job: unknown) => {
      if (typeof job !== "object" || job === null)
        throw new Error("Invalid job");
      const data = job as Record<string, unknown>;
      if (
        typeof data.id !== "string" ||
        data.id.length > 36 ||
        !["worker_check", "ingest"].includes(String(data.kind)) ||
        typeof data.state !== "string" ||
        !states.includes(data.state) ||
        typeof data.progress !== "number" ||
        data.progress < 0 ||
        data.progress > 100 ||
        typeof data.attempts !== "number" ||
        data.attempts < 0 ||
        data.attempts > 5
      )
        throw new Error("Invalid job");
      return {
        id: data.id,
        kind: data.kind,
        state: data.state,
        progress: data.progress,
        attempts: data.attempts,
      };
    });
    return NextResponse.json(safe, { headers });
  } catch {
    return NextResponse.json(
      { detail: "Job service unavailable" },
      { status: 503, headers },
    );
  }
}
