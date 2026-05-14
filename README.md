# KIMY — Revisión inteligente de tesis

Plataforma web y móvil para gestión, revisión y evaluación automatizada de avances de tesis universitarias. Compara documentos contra un patrón institucional, evalúa estructura y calidad con IA, detecta similitudes con pgvector y valida citas bibliográficas con CrossRef.

> Documento de arquitectura, decisiones y fases: **[IMPLEMENTATION.md](IMPLEMENTATION.md)**

## Stack

- **Web**: Next.js 16 (App Router, Turbopack), React 19, TypeScript 5, Tailwind 4, shadcn-style UI
- **API**: FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- **DB**: PostgreSQL 16 + pgvector + Redis
- **IA**: OpenAI GPT-4o-mini / Anthropic Claude 3.5 Sonnet (fallback heurístico si no hay key)
- **Monorepo**: pnpm + Turborepo
- **Infra dev**: Docker Compose

## Estructura

```
apps/
  web/     # Next.js 16 — UI (estudiante, asesor, coordinador, admin)
  api/     # FastAPI — auth, programas, plantillas, avances, IA, evaluaciones
infra/
  docker-compose.yml
  db/init.sql
.claude/skills/   # Skills de Claude Code para este proyecto (kimy-up, kimy-seed, kimy-test)
```

## Requisitos

- Node >= 20, pnpm >= 11 (`npm i -g pnpm`)
- Python 3.12 + `uv` (`pip install --user uv`)
- Docker Desktop

## Levantar el sistema

```bash
# 1. instalar dependencias
pnpm install
cd apps/api && uv sync && cd ../..

# 2. levantar infra (postgres+pgvector, redis)
docker compose -f infra/docker-compose.yml up -d db redis

# 3. migrar DB
cd apps/api && uv run alembic upgrade head && cd ../..

# 4. arrancar API y web (terminales separadas)
pnpm api:dev         # FastAPI en :8003 (Swagger en /docs)
pnpm dev             # Next.js en :3000
```

## Roles y rutas

| Rol | Home | Funcionalidades |
|-----|------|----------------|
| Estudiante | `/student` | Crear avances, subir versiones, ver evaluación IA |
| Asesor | `/advisor` | Revisar avances asignados, aceptar/modificar/descartar findings |
| Coordinador | `/coordinator` | Subir documentos patrón, configurar rúbricas |
| Administrador | `/admin` | Gestionar programas, usuarios, plantillas |

## Fases entregadas

| Fase | Alcance |
|------|---------|
| 0 | Bootstrap del monorepo: web, API, infra dockerizada |
| 1 | Autenticación (JWT + cookies HttpOnly), 4 roles, sidebar por rol |
| 2 | Documentos patrón institucionales — upload Word/PDF, extracción heurística de estructura |
| 3 | Carga y gestión de avances con versionado, descarga proxied con auth |
| 4 | Pipeline IA: evaluación automática con scores por dimensión, hallazgos accionables, feedback loop del asesor (accept/modify/reject) |

Próximas fases: Plagio con pgvector (5), Validación CrossRef (6), ORCID OAuth (7), Dashboard + reportes (8), Bulk review (9), Fine-tuning (10), Mobile Expo (11).

## Variables de entorno

Copia `apps/api/.env.example` -> `apps/api/.env` y rellena. Si configuras `OPENAI_API_KEY` o `ANTHROPIC_API_KEY` el pipeline IA usa LLM real; si no, usa el evaluador heurístico determinístico.
