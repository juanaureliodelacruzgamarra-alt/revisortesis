# syntax=docker/dockerfile:1.7

# ============================================================================
# KIMY web — multi-stage build for Next.js 16
# ============================================================================
# Stage 1: deps     — install with pnpm using the workspace lockfile
# Stage 2: builder  — produce a standalone .next build
# Stage 3: runner   — minimal runtime image, non-root user, healthcheck
# ============================================================================

# ---- Stage 1: deps -----------------------------------------------------------
FROM node:20-alpine AS deps
RUN corepack enable && corepack prepare pnpm@11.1.2 --activate
WORKDIR /repo

# Copy the monorepo manifests so pnpm resolves the workspace correctly.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json apps/web/
# We don't need apps/api or apps/mobile inside the web image — pass
# placeholders so pnpm-workspace.yaml resolves.
COPY apps/api/package.json apps/api/package.json 2>/dev/null || true
COPY apps/mobile/package.json apps/mobile/package.json 2>/dev/null || true

RUN pnpm install --frozen-lockfile --filter @kimy/web... --ignore-scripts

# ---- Stage 2: builder --------------------------------------------------------
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@11.1.2 --activate
WORKDIR /repo

COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web apps/web

# Pass the API URL at build time so any client-bundled NEXT_PUBLIC_API_URL is baked in.
ARG NEXT_PUBLIC_API_URL=http://localhost:8005
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Telemetry off + production build.
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter @kimy/web build

# ---- Stage 3: runner ---------------------------------------------------------
FROM node:20-alpine AS runner
RUN apk add --no-cache curl tini \
    && addgroup -S nextjs -g 1001 \
    && adduser -S nextjs -G nextjs -u 1001
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Copy Next.js' standalone output (must be enabled in next.config.ts).
COPY --from=builder --chown=nextjs:nextjs /repo/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=nextjs:nextjs /repo/apps/web/public ./apps/web/public

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:3000/ || exit 1

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "apps/web/server.js"]
