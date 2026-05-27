import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8005";

// CSP is strict but pragmatic:
// - 'self' for own assets
// - 'unsafe-inline' on style-src for Tailwind's inline keyframes / variables
// - 'unsafe-inline' + 'unsafe-eval' on script-src ONLY in development (Next.js
//   HMR / Fast Refresh injects inline scripts). Production gets a hashless
//   stricter policy without 'unsafe-eval'.
// - connect-src includes the API URL so fetch() works across origins.
const isDev = process.env.NODE_ENV !== "production";

const csp = [
  "default-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
  `img-src 'self' data: blob: ${API_URL}`,
  `font-src 'self' data:`,
  `style-src 'self' 'unsafe-inline'`,
  isDev
    ? `script-src 'self' 'unsafe-inline' 'unsafe-eval'`
    : `script-src 'self' 'unsafe-inline'`,
  `connect-src 'self' ${API_URL} https://api.crossref.org https://orcid.org https://sandbox.orcid.org`,
  "upgrade-insecure-requests",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "no-referrer" },
  {
    key: "Permissions-Policy",
    value: "geolocation=(), microphone=(), camera=()",
  },
  // HSTS only in production behind HTTPS.
  ...(isDev
    ? []
    : [
        {
          key: "Strict-Transport-Security",
          value: "max-age=31536000; includeSubDomains; preload",
        },
      ]),
];

const nextConfig: NextConfig = {
  // NOTE: "standalone" output is only needed for Docker deployments.
  // Vercel handles the build pipeline natively — do NOT set output here.
  // If deploying via Docker, uncomment the line below:
  // output: "standalone",
  async headers() {
    return [
      {
        // Apply to every route. Per-route exemptions go above this entry.
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
