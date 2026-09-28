import type { NextConfig } from "next";
import path from "node:path";

// Remote dev access — a tailnet host, a tunnel, an IP — needs the hostname the
// browser actually uses in two places: `allowedDevOrigins`, so the dev server
// serves its own chunks instead of 403-ing them (Next blocks cross-origin
// requests to dev assets by default), and `connect-src`, so the page may open
// the LangGraph and terminal sockets there. Entries are bare hostnames: the
// Origin match ignores scheme and port. Empty by default, which keeps the
// local-only behaviour. Set in clients/web/.env, e.g.
//   DECEPTICON_DEV_ORIGINS="100.82.166.88,kali.example.ts.net"
const devOrigins = (process.env.DECEPTICON_DEV_ORIGINS ?? "")
  .split(",")
  .map((host) => host.trim())
  .filter(Boolean);

const devConnectSrc = devOrigins.flatMap((host) => [
  `http://${host}:*`,
  `ws://${host}:*`,
]);

const nextConfig: NextConfig = {
  output: "standalone",
  allowedDevOrigins: devOrigins,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: blob:",
              "font-src 'self' data:",
              ["connect-src", "'self'", "ws://localhost:*", "http://localhost:*", ...devConnectSrc].join(" "),
              "frame-ancestors 'none'",
            ].join("; "),
          },
        ],
      },
      // HTML pages: no cache so hotswap chunk name changes take effect immediately
      {
        source: "/:path((?!_next/static|_next/image|favicon.ico).*)",
        headers: [
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
        ],
      },
    ];
  },
  // Pin Turbopack workspace root to the monorepo root (where npm workspaces
  // hoist node_modules). Without this, Turbopack can't resolve `next` since
  // it's not in clients/web/node_modules anymore.
  turbopack: {
    root: path.resolve(process.cwd(), "..", ".."),
  },
  // Packages that must NOT be bundled — left as external Node.js requires.
  // @prisma/client + pg: Turbopack otherwise aliases them with content hashes
  // (e.g. @prisma/client-2c3a…) which the standalone build can't resolve at runtime.
  serverExternalPackages: ["@prisma/client", "pg", "node-pty", "ws"],
  // Do not expose raw LangGraph rewrites from the public web app. Browser
  // clients should use localhost-only LangGraph URLs in local deployments
  // or authenticated server-side route handlers in hosted deployments.
};

export default nextConfig;
