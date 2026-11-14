import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET } from "../app/api/jobs/route";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("job proxy boundary", () => {
  it("rejects unauthenticated requests without contacting the API", async () => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    const response = await GET(
      new NextRequest("https://app.example.test/api/jobs"),
    );
    expect(response.status).toBe(401);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("forwards only the session cookie and strips internal job fields", async () => {
    vi.stubEnv("RAG_INTERNAL_API_URL", "http://api:8000");
    const fetcher = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "job",
            kind: "worker_check",
            state: "running",
            attempts: 1,
            progress: 10,
            lease_token: "internal",
          },
        ]),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetcher);
    const response = await GET(
      new NextRequest("https://app.example.test/api/jobs", {
        headers: { Cookie: "__Host-rag_session=synthetic; unrelated=private" },
      }),
    );
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(await response.text()).not.toContain("internal");
    expect(fetcher.mock.calls[0][1].headers.Cookie).toBe(
      "__Host-rag_session=synthetic",
    );
  });
  it("never reflects backend errors or follows redirects", async () => {
    vi.stubEnv("RAG_INTERNAL_API_URL", "http://api:8000");
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response("private stack details", { status: 500 }),
      );
    vi.stubGlobal("fetch", fetcher);
    const response = await GET(
      new NextRequest("https://app.example.test/api/jobs", {
        headers: { Cookie: "__Host-rag_session=synthetic" },
      }),
    );
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain("private");
    expect(fetcher.mock.calls[0][1].redirect).toBe("error");
  });
});
