# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# uv for fast deterministic installs
RUN pip install --no-cache-dir uv==0.11.14

WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system --no-cache .

COPY src ./src
COPY tests ./tests

EXPOSE 8000

CMD ["uvicorn", "kimy.main:app", "--host", "0.0.0.0", "--port", "8000"]
