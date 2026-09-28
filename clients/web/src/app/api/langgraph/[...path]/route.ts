import { NextRequest, NextResponse } from "next/server";

/**
 * Same-origin mirror of the LangGraph API.
 *
 * The browser used to call LangGraph directly on `http://localhost:2024`,
 * which only works when the browser runs on the same machine as the stack —
 * remotely, "localhost" is the viewer's own host. Proxying through this route
 * keeps every browser request on the page's own origin, so remote dev needs
 * no extra port exposed and no CSP hole. Server-side code keeps using
 * `LANGGRAPH_API_URL` over loopback.
 *
 * Streaming matters here: `/runs/stream` is SSE and stays open for the whole
 * run, so the upstream body is piped through untouched rather than buffered.
 */

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const LANGGRAPH_URL = (process.env.LANGGRAPH_API_URL ?? "http://localhost:2024").replace(/\/$/, "");

// Length and hop-by-hop headers describe the upstream connection, not the
// streamed reply we hand back — forwarding them truncates or corrupts it.
const STRIPPED_RESPONSE_HEADERS = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "keep-alive",
  "transfer-encoding",
]);

interface RouteContext {
  params: Promise<{ path: string[] }>;
}

async function forward(request: NextRequest, { params }: RouteContext): Promise<Response> {
  const { path } = await params;
  const search = new URL(request.url).search;
  const target = `${LANGGRAPH_URL}/${path.join("/")}${search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");

  const hasBody = request.method !== "GET" && request.method !== "HEAD";

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      // Node's fetch requires this whenever the request body is a stream.
      duplex: hasBody ? "half" : undefined,
      redirect: "manual",
      // Abort the upstream call when the browser goes away (tab closed mid-run).
      signal: request.signal,
    } as RequestInit);
  } catch (err) {
    const detail = err instanceof Error ? err.message : "unreachable";
    return NextResponse.json(
      { error: `LangGraph unreachable at ${LANGGRAPH_URL}: ${detail}` },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!STRIPPED_RESPONSE_HEADERS.has(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
export const OPTIONS = forward;
