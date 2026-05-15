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
| 5 | Detección de plagio intra-programa con pgvector (HNSW cosine) |
| 6 | Validación de citas con CrossRef + clasificación verified/partial/not_found/hallucinated |
| 7 | ORCID OAuth (real o stub), sync de publicaciones, advisor-fit por similitud temática |
| 8 | Dashboard de coordinador, KPIs, charts (recharts), acta PDF (reportlab) |
| 9 | Revisión por lotes (reprocess/set_status/assign_advisor) + reporte CSV comparativo |
| 10 | Pipeline de fine-tuning: export JSONL, integración OpenAI Fine-Tuning API, toggle A/B |
| 11 | App móvil con Expo SDK 52: login, mis avances, detalle con findings, perfil, push tokens |

## Mobile app

Stack: Expo SDK 52, React Native 0.76, expo-router, expo-notifications, expo-secure-store.

```bash
# 1. Configura el URL del API que el dispositivo verá
cp apps/mobile/.env.example apps/mobile/.env
# edita EXPO_PUBLIC_API_URL según tu setup:
#   - Android emulator (Studio):  http://10.0.2.2:8005  (default)
#   - iOS simulator:              http://localhost:8005
#   - Dispositivo real en Wi-Fi:  http://<LAN-IP>:8005

# 2. Arranca Metro
pnpm --filter @kimy/mobile start

# 3. Escanea el QR con Expo Go (iOS/Android) o presiona `a` / `i` / `w`
```

Pantallas: `/login` -> tabs (Inicio · Avances · Perfil) -> detalle de avance con findings agrupados por severidad. Push tokens se registran automáticamente al login (si el dispositivo es físico y otorga permiso).

## Variables de entorno

Copia `apps/api/.env.example` -> `apps/api/.env` y rellena. Si configuras `OPENAI_API_KEY` o `ANTHROPIC_API_KEY` el pipeline IA usa LLM real; si no, usa el evaluador heurístico determinístico.
