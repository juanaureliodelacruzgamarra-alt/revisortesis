# syntax=docker/dockerfile:1.7

# ============================================================================
# KIMY API — multi-stage build for FastAPI
# ============================================================================
# Stage 1: deps   — uv resolves the locked Python deps into a virtualenv
# Stage 2: api-runner — slim runtime image, non-root, healthcheck, uvicorn workers
# ============================================================================

# ---- Stage 1: deps -----------------------------------------------------------
FROM python:3.12-slim AS deps

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv==0.11.14

WORKDIR /app

# Install dependencies first (best cache) — without the application source.
COPY pyproject.toml uv.lock ./
RUN uv venv /app/.venv \
 && uv sync --frozen --no-install-project

# Then copy + install the app itself for the editable bits.
COPY src ./src
RUN uv pip install --no-deps .


# ---- Stage 2: api-runner -----------------------------------------------------
FROM python:3.12-slim AS api-runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl tini \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 1001 kimy \
 && useradd --system --uid 1001 --gid kimy --home /app --shell /usr/sbin/nologin kimy

WORKDIR /app

# Copy the virtualenv + the source tree from the deps stage.
COPY --from=deps --chown=kimy:kimy /app/.venv /app/.venv
COPY --from=deps --chown=kimy:kimy /app/src /app/src
COPY --chown=kimy:kimy alembic.ini ./
COPY --chown=kimy:kimy alembic ./alembic

USER kimy
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
# Two worker processes is a sensible default for a single-core node; tune
# via the orchestrator (env GUNICORN_WORKERS) once you know the load.
CMD ["sh", "-c", "alembic upgrade head && uvicorn kimy.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]
