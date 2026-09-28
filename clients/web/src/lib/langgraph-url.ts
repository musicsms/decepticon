/**
 * Resolve the LangGraph API base URL for the current runtime.
 *
 * The browser never talks to LangGraph directly. `api/langgraph/[...path]`
 * mirrors the upstream API on this app's own origin, so a browser on another
 * host (tailnet, tunnel, remote dev) needs no extra port exposed, no
 * cross-origin CSP allowance and no host-dependent base URL — it just calls
 * back into the app it was served from.
 *
 * Server-side callers keep talking to the internal address over loopback.
 * `NEXT_PUBLIC_LANGGRAPH_API_URL` still wins when set: the containerised web
 * image passes it in compose, where the browser can reach the port directly.
 */
export const LANGGRAPH_PROXY_PATH = "/api/langgraph";

export function langgraphApiUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_LANGGRAPH_API_URL;
  if (explicit) return explicit;

  if (typeof window !== "undefined") {
    return new URL(LANGGRAPH_PROXY_PATH, window.location.origin).toString();
  }

  return process.env.LANGGRAPH_API_URL ?? "http://localhost:2024";
}
