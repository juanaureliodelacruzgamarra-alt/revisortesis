---
name: kimy-up
description: Start the full KIMY local stack — Docker (Postgres+pgvector, Redis), FastAPI on 8002, and Next.js on 3000 — in the right order. Verifies each layer responds before moving on. Use at the start of a coding session.
allowed-tools: Bash
---

# Start KIMY stack

Bring up the three layers **sequentially** (each one must be healthy before the next starts) from the repo root.

Repo root: `c:\Users\Crishtian Paz\Desktop\UNT\ciclo 2026-1\Tesis 1\REVISIONTESIS`

## 1. Postgres + pgvector + Redis (Docker)

Start containers and wait for the DB to accept connections:

```bash
cd "/c/Users/Crishtian Paz/Desktop/UNT/ciclo 2026-1/Tesis 1/REVISIONTESIS" && docker compose -f infra/docker-compose.yml up -d db redis
until docker exec kimy-db pg_isready -U kimy -d kimy >/dev/null 2>&1; do sleep 1; done
echo "DB READY"
```

If `docker info` fails, Docker Desktop is not running — start it with:
```bash
powershell.exe -Command "Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'"
```
then poll `until docker info >/dev/null 2>&1; do sleep 2; done` before retrying compose.

## 2. FastAPI on port 8003

Skip if port 8003 already has a listener. Otherwise start in background:

```bash
cd "/c/Users/Crishtian Paz/Desktop/UNT/ciclo 2026-1/Tesis 1/REVISIONTESIS/apps/api" && py -3.12 -m uv run --active -- uvicorn kimy.main:app --host 0.0.0.0 --port 8003 --reload --reload-dir src
```

Run this with `run_in_background: true`. Then wait:
```bash
until curl -sf http://localhost:8003/health >/dev/null 2>&1; do sleep 1; done
echo "API READY"
```

## 3. Next.js on port 3000

Skip if port 3000 already has a listener. Otherwise:

```bash
cd "/c/Users/Crishtian Paz/Desktop/UNT/ciclo 2026-1/Tesis 1/REVISIONTESIS" && pnpm --filter @kimy/web dev
```

Run with `run_in_background: true`. Then wait:
```bash
until curl -sf http://localhost:3000 >/dev/null 2>&1; do sleep 1; done
echo "WEB READY"
```

## Final report

Print this summary to the user:
```
✓ DB    : postgres+pgvector on :5433
✓ Redis : :6379
✓ API   : http://localhost:8003 (docs at /docs)
✓ Web   : http://localhost:3000
```
