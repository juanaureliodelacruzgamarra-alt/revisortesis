# KIMY — Plan de Implementación

> Sistema web + móvil para gestión, revisión y evaluación automatizada de avances de tesis universitarias, con IA (LLM), detección de plagio (pgvector), validación bibliográfica (CrossRef) y vinculación de identidad académica (ORCID).

Documento vivo. Toda decisión arquitectónica relevante queda registrada aquí. Cambios de stack o de scope se reflejan primero en este archivo, después en el código.

---

## 1. Decisiones de arquitectura (resueltas)

Estas tres decisiones resuelven contradicciones del brief original. Si alguna no te convence, vetala antes de implementar.

| # | Tema | Brief original | Decisión final | Razón |
|---|------|----------------|----------------|-------|
| D1 | Next.js | "Next.js 15" | **Next.js 16.2.6** | Ya está instalado, es la versión actual estable. `AGENTS.md` obliga a leer `node_modules/next/dist/docs/` por breaking changes — eso aplica igual en 15 o 16. |
| D2 | Backend | FastAPI + Celery + **Prisma Migrate + BullMQ** (mezcla incompatible) | **FastAPI + Celery + SQLAlchemy 2.0 + Alembic** (100% Python) | Prisma/BullMQ son Node. El brief enfatiza FastAPI como stack principal. Alembic reemplaza Prisma Migrate, Celery reemplaza BullMQ. |
| D3 | Estructura | "Monorepo Turborepo `apps/* packages/*`" pero hoy plano | **Monorepo pnpm + Turborepo** desde ya | Reestructurar antes de tener código es barato; hacerlo después no. |
| D4 | Gestor de paquetes JS | npm (instalado) | **pnpm** (Turborepo lo prefiere, mucho más rápido con monorepos) | El `node_modules` actual se borra cuando movamos código a `apps/web`. |
| D5 | Gestor de paquetes Python | (sin definir) | **uv** | 10-100x más rápido que pip, lockfile reproducible, ya estándar en 2026. |

---

## 2. Stack tecnológico (final)

### 2.1 Frontend Web — `apps/web`
- Next.js 16.2.6 (App Router, Server Components, Turbopack)
- React 19.2.4
- TypeScript 5
- Tailwind CSS 4 (vía `@tailwindcss/postcss`)
- shadcn/ui (Radix + Tailwind)
- TanStack Query 5 (estado de servidor)
- React Hook Form + Zod (formularios y validación)
- next-auth v5 / Auth.js (sesión JWT compartida con la API)
- PDF.js (preview de PDFs)
- recharts (gráficos)
- socket.io-client o EventSource (notificaciones en tiempo real)

### 2.2 Backend API — `apps/api`
- Python 3.12+
- FastAPI (ASGI, uvicorn en dev, gunicorn+uvicorn workers en prod)
- SQLAlchemy 2.0 (ORM async)
- Pydantic v2 (schemas)
- Alembic (migraciones)
- Celery + Redis (jobs asíncronos: IA, plagio, citas)
- python-jose + passlib[bcrypt] (JWT + hashing)
- httpx (clientes HTTP async: ORCID, CrossRef, Copyleaks, OpenAI)
- python-docx, pypdf (extracción de texto)
- LangChain + LlamaIndex (orquestación IA)
- openai SDK (GPT-4o, GPT-4o-mini para fine-tuning)
- anthropic SDK (Claude 3.5 Sonnet como alternativa)
- sentence-transformers o OpenAI embeddings para pgvector
- uv (gestor de paquetes y entornos)
- ruff (lint + format)
- pytest + pytest-asyncio + httpx para tests

### 2.3 Base de datos — `infra/db`
- PostgreSQL 16 + extensión `pgvector` (imagen oficial `pgvector/pgvector:pg16`)
- Redis 7 (broker Celery + caché + pubsub para notificaciones)

### 2.4 Mobile — `apps/mobile`
- Expo SDK 52+
- React Native + TypeScript
- React Navigation (bottom tabs)
- Expo Notifications (push)
- TanStack Query 5
- NativeWind (Tailwind para RN) o React Native Paper — a decidir en M12

### 2.5 Compartido — `packages/`
- `packages/shared-types`: tipos TS generados desde el OpenAPI schema de FastAPI
- `packages/ui`: componentes shadcn/ui reutilizables (web; mobile usa su propia UI)
- `packages/config`: configs compartidas (tsconfig, eslint, prettier)

### 2.6 Infra
- Docker Compose (dev): postgres+pgvector, redis, api, web, worker (Celery), beat (Celery scheduler)
- `.env` files por app, `.env.example` versionado
- GitHub Actions: lint + test en PR

---

## 3. Estructura de directorios objetivo

```
REVISIONTESIS/
├── apps/
│   ├── web/                    # Next.js 16
│   │   ├── src/
│   │   │   ├── app/            # App Router
│   │   │   │   ├── (auth)/     # login, register, recover
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── student/
│   │   │   │   │   ├── advisor/
│   │   │   │   │   ├── coordinator/
│   │   │   │   │   └── admin/
│   │   │   │   ├── api/        # route handlers (BFF: proxy a FastAPI cuando convenga)
│   │   │   │   └── layout.tsx
│   │   │   ├── components/     # atomic design (ui/, molecules/, organisms/)
│   │   │   ├── features/       # carpetas por feature (auth, documents, review, ai, plagiarism…)
│   │   │   ├── hooks/
│   │   │   ├── lib/            # api client, auth, utils
│   │   │   └── styles/
│   │   ├── package.json
│   │   └── next.config.ts
│   │
│   ├── api/                    # FastAPI
│   │   ├── src/
│   │   │   ├── kimy/
│   │   │   │   ├── api/        # routers (uno por módulo)
│   │   │   │   │   ├── v1/
│   │   │   │   │   │   ├── auth.py
│   │   │   │   │   │   ├── users.py
│   │   │   │   │   │   ├── templates.py
│   │   │   │   │   │   ├── documents.py
│   │   │   │   │   │   ├── reviews.py
│   │   │   │   │   │   ├── ai_findings.py
│   │   │   │   │   │   ├── plagiarism.py
│   │   │   │   │   │   ├── citations.py
│   │   │   │   │   │   ├── orcid.py
│   │   │   │   │   │   ├── reports.py
│   │   │   │   │   │   └── stats.py
│   │   │   │   ├── core/       # config, security, deps
│   │   │   │   ├── db/         # session, base, init
│   │   │   │   ├── models/     # SQLAlchemy models
│   │   │   │   ├── schemas/    # Pydantic schemas
│   │   │   │   ├── services/   # lógica de aplicación
│   │   │   │   │   ├── ai/                # pipeline IA (LangChain)
│   │   │   │   │   │   ├── prompts/       # system prompts versionados
│   │   │   │   │   │   ├── pipeline.py
│   │   │   │   │   │   ├── grader.py
│   │   │   │   │   │   └── findings.py
│   │   │   │   │   ├── plagiarism/        # pgvector + Copyleaks
│   │   │   │   │   ├── citations/         # CrossRef
│   │   │   │   │   ├── orcid/             # OAuth + API pública
│   │   │   │   │   ├── documents/         # extracción y parsing
│   │   │   │   │   └── fine_tuning/       # export JSONL + activación
│   │   │   │   ├── workers/    # Celery tasks
│   │   │   │   ├── utils/
│   │   │   │   └── main.py     # FastAPI app
│   │   ├── alembic/
│   │   │   └── versions/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── mobile/                 # Expo
│       ├── app/                # Expo Router
│       ├── components/
│       ├── features/
│       ├── lib/
│       └── package.json
│
├── packages/
│   ├── shared-types/           # tipos TS auto-generados desde OpenAPI
│   ├── ui/                     # shadcn components reutilizables (web)
│   └── config/                 # tsconfig, eslint, prettier base
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── db/
│       └── init.sql            # CREATE EXTENSION vector;
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AI_PIPELINE.md
│   ├── PROMPTS.md
│   ├── ORCID_SETUP.md
│   ├── COPYLEAKS_SETUP.md
│   └── FINE_TUNING.md
│
├── .github/workflows/
├── turbo.json
├── pnpm-workspace.yaml
├── package.json                # raíz del monorepo
├── README.md
├── AGENTS.md
├── CLAUDE.md
└── IMPLEMENTATION.md           # este archivo
```

---

## 4. Modelo de datos (resumen ER)

PostgreSQL 16 + `pgvector`. SQLAlchemy 2.0 con tipos modernos (`Mapped`, `mapped_column`). Alembic para migraciones.

### Tablas principales

```
users (PK id, email, password_hash, role, created_at, ...)
  └─ role ∈ {student, advisor, coordinator, admin}

advisor_profiles (PK user_id FK→users)
  ├─ orcid_id
  ├─ orcid_access_token       (cifrado AES-256)
  ├─ orcid_refresh_token      (cifrado AES-256)
  ├─ orcid_last_sync
  └─ affiliation

orcid_publications (PK id, advisor_id FK, doi, title, year, journal, embedding vector(1536))

student_profiles (PK user_id FK→users, program_id FK→academic_programs, advisor_id FK→users nullable)

academic_programs (PK id, name, level)              # maestría, doctorado, pregrado por área

template_documents (PK id, program_id FK, version, file_url, structure_json, rubric_json, created_by, active)
  └─ structure_json: secciones, orden, extensión, formato citas
  └─ rubric_json: pesos por dimensión, criterios, escala

submissions (PK id, student_id FK, template_id FK, title, type, status, created_at)
  └─ status ∈ {pending, ai_processing, human_review, observed, approved, rejected}

submission_versions (PK id, submission_id FK, version_number, file_url, page_count, uploaded_at)

ai_evaluations (PK id, version_id FK UNIQUE, model, prompt_version,
                structure_score, content_score, form_score, originality_score,
                total_percentage, decimal_grade, executive_summary, created_at, duration_ms)

ai_findings (PK id, evaluation_id FK,
             section, page_approx, type, severity,
             description, instruction, example, recommendation,
             human_action,            # null | accepted | modified | rejected
             human_comment,           # texto si modified/rejected
             human_severity_override, # si humano ajusta severidad
             reviewed_by FK→users nullable,
             reviewed_at)
  └─ severity ∈ {critical, major, minor, suggestion}
  └─ index (evaluation_id), (human_action) para export fine-tuning

document_chunks (PK id, version_id FK, section, chunk_index,
                 text, embedding vector(1536))
  └─ ivfflat index on embedding (vector_cosine_ops)

plagiarism_matches (PK id, version_id FK, matched_version_id FK,
                    matched_chunk_id FK, similarity, source,  # intra | copyleaks
                    reviewed_by, status)

citations (PK id, version_id FK,
           raw_text, title, authors, year, journal, doi,
           crossref_status,    # verified | partial | not_found | hallucinated
           crossref_metadata jsonb,
           checked_at)

human_reviews (PK id, version_id FK, reviewer_id FK→users,
               rubric_filled jsonb, final_grade, decision, comments, created_at)

annotations (PK id, version_id FK, reviewer_id FK, page, paragraph, text, type)

submission_state_logs (PK id, submission_id FK, from_state, to_state, actor_id, occurred_at)

audit_logs (PK id, actor_id, action, entity_type, entity_id, diff jsonb, ip, ua, occurred_at)

notifications (PK id, user_id FK, type, payload jsonb, read_at, created_at)

push_tokens (PK id, user_id FK, expo_push_token, device, last_seen)

fine_tuning_jobs (PK id, dataset_jsonl_url, openai_job_id, status, created_by, created_at)

system_settings (PK key, value jsonb, updated_by, updated_at)
  └─ p.ej. copyleaks_api_key (cifrado), grading_scale_max, ai_active_model
```

Índices clave:
- `document_chunks.embedding` ivfflat (cosine) — búsqueda de plagio en O(log n) sobre miles de avances.
- `orcid_publications.embedding` ivfflat — match temático asesor↔tesis.
- `ai_findings (evaluation_id, severity)` — listado priorizado.
- `submissions (student_id, status)`, `submissions (template_id, created_at)`.

---

## 5. Pipeline de IA (Módulo 5 — corazón del sistema)

Encolado en Celery cuando `submission_versions.uploaded_at` se inserta.

```
[upload] → enqueue ai.evaluate_version(version_id)

ai.evaluate_version
  1. extract_text(version_id)               # python-docx / pypdf
  2. parse_structure(text, template)        # LLM con prompt estructurado
  3. chunk_and_embed(text)                  # → document_chunks (pgvector)
  4. detect_missing_sections(structure, template.structure_json)
  5. detect_errors(text, template)          # LLM, prompt findings
  6. semantic_coherence(text)               # LLM, prompt semántico
  7. grade(scores)                          # estructura 30 / contenido 40 / forma 20 / originalidad 10
  8. executive_summary(text, findings, grade)
  9. persist ai_evaluation + ai_findings
 10. fanout:
       - enqueue plagiarism.scan_version(version_id)
       - enqueue citations.extract_and_verify(version_id)
 11. notify(student) + websocket update(advisor dashboard)
```

Prompts versionados en `apps/api/src/kimy/services/ai/prompts/` (carpeta `v1/`, `v2/`…) — cada ai_evaluation registra `prompt_version` para reproducibilidad y A/B.

### Feedback loop → fine-tuning

- Endpoint admin: `POST /api/v1/admin/fine-tuning/export` → genera JSONL desde `ai_findings` donde `human_action IN ('modified','rejected')` o con cambio de severidad.
- Formato OpenAI Chat Fine-tuning (`messages: [system, user, assistant]`), donde `assistant` es la versión corregida por el humano.
- Trigger automático al alcanzar 500 ejemplos validados (alerta, no auto-submit).
- Alternativa local: clasificador de severidad con scikit-learn / sentence-transformers, servido por endpoint dedicado.
- Toggle en `system_settings.ai_active_model` para A/B.

---

## 6. Servicios externos

| Servicio | Uso | Notas |
|----------|-----|-------|
| OpenAI | GPT-4o (evaluación), text-embedding-3-small (1536 dims, pgvector) | Default. Fine-tuning sobre gpt-4o-mini. |
| Anthropic | Claude 3.5 Sonnet | Alternativa para evaluación; toggle por modelo. |
| ORCID | OAuth 2.0 + API pública | Public API no requiere member account. Tokens cifrados AES-256. |
| CrossRef | `api.crossref.org/works` | **Política de cortesía: 1 req/s** — implementar con `httpx` + `asyncio.Semaphore` + email en header `User-Agent`. |
| Copyleaks | Opcional | Solo si el admin configura API key en `system_settings`. |
| Expo Push | Notificaciones móvil | `expo-server-sdk` (Python) para enviar push. |

---

## 7. Seguridad y no-funcionales

- Passwords: bcrypt cost 12.
- JWT: HS256 con secret rotado, access 15min + refresh 30 días.
- Tokens ORCID y Copyleaks API key: cifrados con `cryptography` Fernet (AES-128-CBC + HMAC) usando `SECRET_ENCRYPTION_KEY`.
- Rate limiting: `slowapi` en FastAPI (login 5/min, upload 10/min, IA jobs por user).
- Validación: Pydantic v2 en API, Zod en web, RHF + Zod en formularios.
- CORS: whitelist explícita (`apps/web` URL, mobile no necesita CORS).
- Archivos: almacenamiento local en dev (`./storage/`), S3-compatible en prod (MinIO local opcional). Validar mime + size + virus scan opcional (clamav).
- Audit log: middleware FastAPI que inserta en `audit_logs` para mutaciones.
- WCAG 2.1 AA: shadcn/ui ya cumple base; revisar contraste y navegación teclado por feature.

---

## 8. Roadmap por fases

Cada fase tiene un **criterio de "done"** verificable. No avanzamos sin él.

### Fase 0 — Bootstrap (1 sesión)
- [ ] Mover el Next.js actual a `apps/web/`
- [ ] Inicializar pnpm workspace + Turborepo
- [ ] Crear `apps/api/` con FastAPI hello world
- [ ] Crear `infra/docker-compose.yml` (postgres+pgvector, redis, api, web)
- [ ] `.env.example` para web y api
- [ ] `pnpm dev` levanta web; `docker compose up` levanta toda la stack
- **Done:** http://localhost:3000 (web) y http://localhost:8003/docs (FastAPI Swagger) responden.

### Fase 1 — Auth y usuarios (Módulo 1 sin ORCID)
- [ ] Modelos `users`, `student_profiles`, `advisor_profiles`, `academic_programs`
- [ ] Alembic init + primera migración
- [ ] Endpoints: register, login, refresh, me, recover password (sin email aún, token devuelto)
- [ ] Web: páginas `/login`, `/register`, `/recover`, layout dashboard básico con sidebar por rol
- [ ] Middleware de protección de rutas por rol en web
- **Done:** crear estudiante + asesor + coordinador, login en web, dashboard vacío visible.

### Fase 2 — Documentos patrón (Módulo 2)
- [ ] CRUD `template_documents` (solo coordinador/admin)
- [ ] Upload Word/PDF → extracción de `structure_json` con LLM
- [ ] UI coordinator: subir patrón, ver versiones, editar rúbrica
- **Done:** un coordinador sube un Word, el sistema extrae secciones, queda activo para un programa.

### Fase 3 — Carga de avances (Módulo 4)
- [ ] CRUD `submissions` + `submission_versions`
- [ ] Upload con validación (50MB, Word/PDF)
- [ ] Preview con PDF.js
- [ ] Encolado a Celery (placeholder de IA, solo marca `ai_processing` y termina)
- **Done:** un estudiante sube un Word, lo ve previsualizado, queda en estado `ai_processing`.

### Fase 4 — Pipeline IA (Módulo 5, core)
- [ ] Extracción de texto (docx + pdf)
- [ ] Prompts versionados v1 (estructura, errores, semántica, ejecutivo)
- [ ] `ai_evaluations` + `ai_findings` poblados
- [ ] UI revisión lado a lado (Módulo 6 mínimo): doc izquierda, hallazgos derecha
- [ ] Acciones del asesor: accept / modify / reject por hallazgo (Módulo 5.5)
- **Done:** subir un avance produce evaluación IA realista en <30s y el asesor puede revisarla.

### Fase 5 — Plagio (Módulo 8)
- [ ] Embeddings de chunks → pgvector
- [ ] Job `plagiarism.scan_version` con consulta de similitud coseno
- [ ] `plagiarism_matches` + hallazgo automático severidad mayor
- [ ] UI: panel de matches en review
- **Done:** dos avances con 2 párrafos copiados generan un match >0.85 visible.

### Fase 6 — Citas con CrossRef (Módulo 9)
- [ ] Extracción de referencias con prompt
- [ ] Cliente CrossRef con rate limiting 1 req/s
- [ ] Job `citations.extract_and_verify`
- [ ] UI: lista de citas con estado y sugerencia
- **Done:** un avance con 5 referencias (3 reales, 2 inventadas) clasifica correctamente.

### Fase 7 — ORCID (Módulo 1.ORCID)
- [ ] OAuth flow (botón "Vincular ORCID" → callback)
- [ ] Sync publicaciones + embeddings
- [ ] Validación cruzada asesor↔tesis con alerta a coordinador
- **Done:** un asesor vincula ORCID, sus papers quedan en DB, asignarlo a una tesis de otro tema dispara alerta.

### Fase 8 — Dashboard, reportes, stats (Módulos 3, 10, 11)
- [ ] KPIs, filtros, timeline
- [ ] Generación PDF de actas
- [ ] Gráficos (recharts)
- [ ] Notificaciones en tiempo real (SSE primero, websocket si hace falta)
- **Done:** coordinador ve KPIs reales, exporta actas, recibe notificación cuando termina un job.

### Fase 9 — Bulk review (Módulo 7)
- [ ] Selección múltiple + encolado masivo
- [ ] Barra de progreso (SSE)
- [ ] Reportes comparativos de lotes
- **Done:** 20 avances procesados en bulk con ranking final.

### Fase 10 — Fine-tuning (Módulo 5.5 pipeline)
- [ ] Endpoint export JSONL
- [ ] Trigger automático a 500 ejemplos
- [ ] Toggle modelo activo
- [ ] Doc en `docs/FINE_TUNING.md`
- **Done:** export descarga JSONL válido, comando `openai fine_tunes.create` documentado.

### Fase 11 — Mobile (Módulo 12)
- [ ] Expo init en `apps/mobile/`
- [ ] Login compartido (JWT)
- [ ] Tabs: Inicio, Mis Revisiones, Detalle, Historial, Reportes
- [ ] Push con `expo-server-sdk`
- **Done:** app corre en Expo Go, ve hallazgos, recibe push de "revisión IA lista".

### Fase 12 — Hardening
- [ ] Tests críticos (pytest API + Playwright web)
- [ ] CI GitHub Actions
- [ ] Auditoría seguridad (rate limit, headers, OWASP top 10)
- [ ] README final + docs/*

---

## 9. Variables de entorno (referencia)

`apps/api/.env`:
```
DATABASE_URL=postgresql+asyncpg://kimy:kimy@db:5432/kimy
REDIS_URL=redis://redis:6379/0
JWT_SECRET=...
ENCRYPTION_KEY=...                  # Fernet key, 32 bytes base64
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
ORCID_CLIENT_ID=...
ORCID_CLIENT_SECRET=...
ORCID_REDIRECT_URI=http://localhost:3000/orcid/callback
CROSSREF_USER_AGENT=KIMY/0.1 (mailto:tu@correo)
COPYLEAKS_API_KEY=                  # opcional, lo configura admin en runtime
STORAGE_BACKEND=local               # local | s3
STORAGE_PATH=./storage
CORS_ORIGINS=http://localhost:3000
```

`apps/web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8003
NEXTAUTH_SECRET=...
NEXTAUTH_URL=http://localhost:3000
```

`apps/mobile/.env`:
```
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000   # android emulator
```

---

## 10. Convenciones

- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`).
- **Branches:** `main` (protegida) + `feat/m{n}-{slug}` por feature.
- **PRs:** descripción + screenshots (web) + checklist done.
- **Tests críticos:** auth, pipeline IA, plagio, citas, ORCID.
- **Estilo:** ruff (api), eslint+prettier (web/mobile), import order automático.
- **Idioma:** UI en español, código y comentarios en inglés, errores de API en inglés con `code` enum y traducción en frontend.

---

## 11. Riesgos abiertos

| Riesgo | Mitigación |
|--------|------------|
| Costo OpenAI alto con muchos avances | Cache de evaluaciones por `hash(version_file)`. Modelo dual GPT-4o-mini default, GPT-4o solo si confianza baja. |
| Falsos positivos de plagio en intro/marco teórico (citas comunes) | Excluir secciones marcadas como "marco teórico" del scan, o subir umbral a 0.90 para esas. |
| Rate limit CrossRef en lotes grandes | Worker dedicado con semáforo global, cola priorizada. |
| ORCID tokens expirando | Refresh automático en background; capturar 401 y re-autorizar. |
| Tamaño pgvector con miles de avances | ivfflat lists tuneado, particionar por `program_id` si crece. |

---

## 12. Próximo paso

Ejecutar **Fase 0 — Bootstrap**: mover el web actual a `apps/web/`, inicializar pnpm + Turborepo, crear `apps/api/` con FastAPI hello world y `infra/docker-compose.yml`.

Confírmame que aceptas las decisiones D1–D5 y arranco con la Fase 0.
