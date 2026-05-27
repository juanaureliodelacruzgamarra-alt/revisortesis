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

```
RevisorTesis
├─ .claude
│  └─ skills
│     ├─ kimy-mobile
│     │  └─ SKILL.md
│     ├─ kimy-seed
│     │  └─ SKILL.md
│     ├─ kimy-test
│     │  └─ SKILL.md
│     └─ kimy-up
│        └─ SKILL.md
├─ .npmrc
├─ AGENTS.md
├─ CLAUDE.md
├─ IMPLEMENTATION.md
├─ README.md
├─ apps
│  ├─ api
│  │  ├─ Dockerfile
│  │  ├─ alembic
│  │  │  ├─ env.py
│  │  │  ├─ script.py.mako
│  │  │  └─ versions
│  │  │     ├─ 0560059db985_phase7_orcid_publications_and_advisor_.py
│  │  │     ├─ 2298185806fd_phase10_fine_tuning_jobs_and_system_.py
│  │  │     ├─ 273dd3290cc0_phase5_document_chunks_and_plagiarism_.py
│  │  │     ├─ 2f67c147d36f_phase3_submissions_and_versions.py
│  │  │     ├─ 7c68e36bc49b_phase4_ai_evaluations_and_ai_findings.py
│  │  │     ├─ 80bbcdae218f_phase2_template_documents.py
│  │  │     ├─ 93c7cf1b6cdf_phase1_users_and_profiles.py
│  │  │     ├─ 95c60583537e_phase11_push_tokens.py
│  │  │     ├─ a59a4f2b578f_phase13_audit_logs.py
│  │  │     └─ f8cb8d18794e_phase6_citations.py
│  │  ├─ alembic.ini
│  │  ├─ pyproject.toml
│  │  ├─ src
│  │  │  └─ kimy
│  │  │     ├─ __init__.py
│  │  │     ├─ api
│  │  │     │  ├─ __init__.py
│  │  │     │  └─ v1
│  │  │     │     ├─ __init__.py
│  │  │     │     ├─ audit.py
│  │  │     │     ├─ auth.py
│  │  │     │     ├─ bulk.py
│  │  │     │     ├─ citations.py
│  │  │     │     ├─ evaluations.py
│  │  │     │     ├─ fine_tuning.py
│  │  │     │     ├─ orcid.py
│  │  │     │     ├─ plagiarism.py
│  │  │     │     ├─ programs.py
│  │  │     │     ├─ push.py
│  │  │     │     ├─ reports.py
│  │  │     │     ├─ settings.py
│  │  │     │     ├─ stats.py
│  │  │     │     ├─ submissions.py
│  │  │     │     ├─ templates.py
│  │  │     │     └─ users.py
│  │  │     ├─ core
│  │  │     │  ├─ __init__.py
│  │  │     │  ├─ audit.py
│  │  │     │  ├─ config.py
│  │  │     │  ├─ crypto.py
│  │  │     │  ├─ deps.py
│  │  │     │  ├─ rate_limit.py
│  │  │     │  └─ security.py
│  │  │     ├─ db
│  │  │     │  ├─ __init__.py
│  │  │     │  ├─ base.py
│  │  │     │  └─ session.py
│  │  │     ├─ main.py
│  │  │     ├─ models
│  │  │     │  ├─ __init__.py
│  │  │     │  ├─ academic_program.py
│  │  │     │  ├─ advisor_profile.py
│  │  │     │  ├─ ai_evaluation.py
│  │  │     │  ├─ ai_finding.py
│  │  │     │  ├─ audit_log.py
│  │  │     │  ├─ citation.py
│  │  │     │  ├─ document_chunk.py
│  │  │     │  ├─ fine_tuning_job.py
│  │  │     │  ├─ orcid_publication.py
│  │  │     │  ├─ plagiarism_match.py
│  │  │     │  ├─ push_token.py
│  │  │     │  ├─ student_profile.py
│  │  │     │  ├─ submission.py
│  │  │     │  ├─ submission_version.py
│  │  │     │  ├─ system_setting.py
│  │  │     │  ├─ template_document.py
│  │  │     │  └─ user.py
│  │  │     ├─ schemas
│  │  │     │  ├─ __init__.py
│  │  │     │  ├─ audit.py
│  │  │     │  ├─ auth.py
│  │  │     │  ├─ bulk.py
│  │  │     │  ├─ citations.py
│  │  │     │  ├─ evaluations.py
│  │  │     │  ├─ fine_tuning.py
│  │  │     │  ├─ orcid.py
│  │  │     │  ├─ plagiarism.py
│  │  │     │  ├─ programs.py
│  │  │     │  ├─ push.py
│  │  │     │  ├─ reports.py
│  │  │     │  ├─ settings.py
│  │  │     │  ├─ stats.py
│  │  │     │  ├─ submissions.py
│  │  │     │  ├─ templates.py
│  │  │     │  └─ users.py
│  │  │     ├─ scripts
│  │  │     │  ├─ __init__.py
│  │  │     │  └─ seed_demo.py
│  │  │     └─ services
│  │  │        ├─ __init__.py
│  │  │        ├─ activity.py
│  │  │        ├─ ai
│  │  │        │  ├─ __init__.py
│  │  │        │  ├─ llm_evaluator.py
│  │  │        │  ├─ pipeline.py
│  │  │        │  ├─ prompts
│  │  │        │  │  ├─ __init__.py
│  │  │        │  │  └─ v1
│  │  │        │  │     └─ __init__.py
│  │  │        │  ├─ schemas.py
│  │  │        │  └─ stub_evaluator.py
│  │  │        ├─ bulk.py
│  │  │        ├─ citations
│  │  │        │  ├─ __init__.py
│  │  │        │  ├─ crossref.py
│  │  │        │  ├─ extractor.py
│  │  │        │  └─ validator.py
│  │  │        ├─ documents
│  │  │        │  ├─ __init__.py
│  │  │        │  ├─ extractor.py
│  │  │        │  └─ structure_parser.py
│  │  │        ├─ evaluations.py
│  │  │        ├─ fine_tuning
│  │  │        │  ├─ __init__.py
│  │  │        │  ├─ exporter.py
│  │  │        │  └─ submitter.py
│  │  │        ├─ orcid
│  │  │        │  ├─ __init__.py
│  │  │        │  ├─ advisor_fit.py
│  │  │        │  ├─ api_client.py
│  │  │        │  ├─ oauth.py
│  │  │        │  └─ sync.py
│  │  │        ├─ plagiarism
│  │  │        │  ├─ __init__.py
│  │  │        │  ├─ chunker.py
│  │  │        │  ├─ embedder.py
│  │  │        │  └─ scanner.py
│  │  │        ├─ programs.py
│  │  │        ├─ push
│  │  │        │  ├─ __init__.py
│  │  │        │  └─ sender.py
│  │  │        ├─ reports
│  │  │        │  ├─ __init__.py
│  │  │        │  ├─ csv_exporter.py
│  │  │        │  ├─ pdf.py
│  │  │        │  ├─ pdf_executive.py
│  │  │        │  ├─ pdf_letterhead.py
│  │  │        │  └─ pdf_reports.py
│  │  │        ├─ settings.py
│  │  │        ├─ stats.py
│  │  │        ├─ storage.py
│  │  │        ├─ submissions.py
│  │  │        ├─ templates.py
│  │  │        └─ users.py
│  │  ├─ tests
│  │  │  ├─ __init__.py
│  │  │  ├─ conftest.py
│  │  │  ├─ test_auth.py
│  │  │  ├─ test_health.py
│  │  │  ├─ test_push.py
│  │  │  └─ test_submissions.py
│  │  └─ uv.lock
│  ├─ mobile
│  │  ├─ .expo
│  │  │  ├─ README.md
│  │  │  └─ devices.json
│  │  ├─ app
│  │  │  ├─ (auth)
│  │  │  │  ├─ _layout.tsx
│  │  │  │  └─ login.tsx
│  │  │  ├─ (tabs)
│  │  │  │  ├─ _layout.tsx
│  │  │  │  ├─ index.tsx
│  │  │  │  ├─ profile.tsx
│  │  │  │  └─ submissions.tsx
│  │  │  ├─ _layout.tsx
│  │  │  └─ submission
│  │  │     ├─ [id].tsx
│  │  │     └─ _layout.tsx
│  │  ├─ app.json
│  │  ├─ babel.config.js
│  │  ├─ lib
│  │  │  ├─ api.ts
│  │  │  ├─ auth.tsx
│  │  │  ├─ env.ts
│  │  │  ├─ push.ts
│  │  │  ├─ storage.ts
│  │  │  └─ types.ts
│  │  ├─ package.json
│  │  └─ tsconfig.json
│  └─ web
│     ├─ Dockerfile
│     ├─ eslint.config.mjs
│     ├─ next.config.ts
│     ├─ package.json
│     ├─ playwright.config.ts
│     ├─ postcss.config.mjs
│     ├─ public
│     │  ├─ file.svg
│     │  ├─ globe.svg
│     │  ├─ next.svg
│     │  ├─ vercel.svg
│     │  └─ window.svg
│     ├─ src
│     │  ├─ app
│     │  │  ├─ (auth)
│     │  │  │  ├─ layout.tsx
│     │  │  │  ├─ login
│     │  │  │  │  └─ page.tsx
│     │  │  │  └─ register
│     │  │  │     └─ page.tsx
│     │  │  ├─ (dashboard)
│     │  │  │  ├─ admin
│     │  │  │  │  ├─ fine-tuning
│     │  │  │  │  │  └─ page.tsx
│     │  │  │  │  ├─ page.tsx
│     │  │  │  │  ├─ programs
│     │  │  │  │  │  └─ page.tsx
│     │  │  │  │  ├─ settings
│     │  │  │  │  │  └─ page.tsx
│     │  │  │  │  └─ users
│     │  │  │  │     └─ page.tsx
│     │  │  │  ├─ advisor
│     │  │  │  │  ├─ page.tsx
│     │  │  │  │  ├─ profile
│     │  │  │  │  │  └─ page.tsx
│     │  │  │  │  └─ reviews
│     │  │  │  │     ├─ [id]
│     │  │  │  │     │  └─ page.tsx
│     │  │  │  │     └─ page.tsx
│     │  │  │  ├─ coordinator
│     │  │  │  │  ├─ page.tsx
│     │  │  │  │  ├─ reports
│     │  │  │  │  │  └─ page.tsx
│     │  │  │  │  ├─ submissions
│     │  │  │  │  │  └─ page.tsx
│     │  │  │  │  └─ templates
│     │  │  │  │     ├─ [id]
│     │  │  │  │     │  └─ page.tsx
│     │  │  │  │     └─ page.tsx
│     │  │  │  ├─ layout.tsx
│     │  │  │  ├─ providers.tsx
│     │  │  │  └─ student
│     │  │  │     ├─ page.tsx
│     │  │  │     ├─ reports
│     │  │  │     │  └─ page.tsx
│     │  │  │     └─ submissions
│     │  │  │        ├─ [id]
│     │  │  │        │  └─ page.tsx
│     │  │  │        ├─ new
│     │  │  │        │  └─ page.tsx
│     │  │  │        └─ page.tsx
│     │  │  ├─ api
│     │  │  │  ├─ fine-tuning
│     │  │  │  │  └─ [jobId]
│     │  │  │  │     └─ dataset.jsonl
│     │  │  │  │        └─ route.ts
│     │  │  │  ├─ reports
│     │  │  │  │  ├─ activity.pdf
│     │  │  │  │  │  └─ route.ts
│     │  │  │  │  ├─ executive.pdf
│     │  │  │  │  │  └─ route.ts
│     │  │  │  │  ├─ programs.csv
│     │  │  │  │  │  └─ route.ts
│     │  │  │  │  ├─ programs.pdf
│     │  │  │  │  │  └─ route.ts
│     │  │  │  │  ├─ submissions.csv
│     │  │  │  │  │  └─ route.ts
│     │  │  │  │  └─ submissions.pdf
│     │  │  │  │     └─ route.ts
│     │  │  │  └─ submissions
│     │  │  │     ├─ [id]
│     │  │  │     │  ├─ report.pdf
│     │  │  │     │  │  └─ route.ts
│     │  │  │     │  └─ versions
│     │  │  │     │     └─ [versionId]
│     │  │  │     │        └─ file
│     │  │  │     │           └─ route.ts
│     │  │  │     └─ batch-report.csv
│     │  │  │        └─ route.ts
│     │  │  ├─ favicon.ico
│     │  │  ├─ globals.css
│     │  │  ├─ layout.tsx
│     │  │  ├─ orcid
│     │  │  │  └─ callback
│     │  │  │     └─ page.tsx
│     │  │  └─ page.tsx
│     │  ├─ components
│     │  │  └─ ui
│     │  │     ├─ badge.tsx
│     │  │     ├─ button.tsx
│     │  │     ├─ card.tsx
│     │  │     ├─ input.tsx
│     │  │     └─ label.tsx
│     │  ├─ features
│     │  │  ├─ auth
│     │  │  │  ├─ auth-split.tsx
│     │  │  │  ├─ login-form.tsx
│     │  │  │  └─ register-form.tsx
│     │  │  ├─ citations
│     │  │  │  └─ citations-panel.tsx
│     │  │  ├─ dashboard
│     │  │  │  ├─ kpi-card.tsx
│     │  │  │  ├─ nav-items.ts
│     │  │  │  ├─ program-bars.tsx
│     │  │  │  ├─ role-home.tsx
│     │  │  │  ├─ sidebar.tsx
│     │  │  │  └─ status-donut.tsx
│     │  │  ├─ evaluations
│     │  │  │  ├─ evaluation-panel.tsx
│     │  │  │  ├─ evaluation-summary.tsx
│     │  │  │  ├─ finding-actions.tsx
│     │  │  │  └─ finding-card.tsx
│     │  │  ├─ fine-tuning
│     │  │  │  ├─ actions-bar.tsx
│     │  │  │  └─ model-toggle.tsx
│     │  │  ├─ orcid
│     │  │  │  └─ link-button.tsx
│     │  │  ├─ plagiarism
│     │  │  │  └─ matches-panel.tsx
│     │  │  ├─ programs
│     │  │  │  ├─ program-form.tsx
│     │  │  │  └─ program-row.tsx
│     │  │  ├─ settings
│     │  │  │  └─ ft-threshold-form.tsx
│     │  │  ├─ submissions
│     │  │  │  ├─ advisor-assign-select.tsx
│     │  │  │  ├─ bulk-toolbar.tsx
│     │  │  │  ├─ filters-bar.tsx
│     │  │  │  ├─ selectable-list.tsx
│     │  │  │  ├─ status-badge.tsx
│     │  │  │  ├─ submission-form.tsx
│     │  │  │  ├─ submission-row.tsx
│     │  │  │  ├─ version-list.tsx
│     │  │  │  └─ version-uploader.tsx
│     │  │  ├─ templates
│     │  │  │  ├─ structure-tree.tsx
│     │  │  │  ├─ template-card.tsx
│     │  │  │  └─ template-form.tsx
│     │  │  └─ users
│     │  │     ├─ user-form.tsx
│     │  │     └─ user-row.tsx
│     │  ├─ lib
│     │  │  ├─ api
│     │  │  │  ├─ citations.ts
│     │  │  │  ├─ client.ts
│     │  │  │  ├─ evaluations.ts
│     │  │  │  ├─ fine-tuning.ts
│     │  │  │  ├─ orcid.ts
│     │  │  │  ├─ plagiarism.ts
│     │  │  │  ├─ programs.ts
│     │  │  │  ├─ reports.ts
│     │  │  │  ├─ settings.ts
│     │  │  │  ├─ stats.ts
│     │  │  │  ├─ submissions.ts
│     │  │  │  ├─ templates.ts
│     │  │  │  ├─ types.ts
│     │  │  │  └─ users.ts
│     │  │  ├─ auth
│     │  │  │  ├─ actions.ts
│     │  │  │  ├─ cookies.ts
│     │  │  │  ├─ session.ts
│     │  │  │  └─ types.ts
│     │  │  ├─ cn.ts
│     │  │  ├─ env.ts
│     │  │  ├─ i18n-provider.tsx
│     │  │  └─ theme-provider.tsx
│     │  └─ middleware.ts
│     ├─ tests
│     │  └─ e2e
│     │     ├─ auth.spec.ts
│     │     ├─ dashboards.spec.ts
│     │     └─ fixtures.ts
│     └─ tsconfig.json
├─ docs
│  ├─ DEPLOY.md
│  ├─ FINE_TUNING.md
│  └─ SECURITY.md
├─ infra
│  ├─ db
│  │  └─ init.sql
│  ├─ docker-compose.prod.yml
│  └─ docker-compose.yml
├─ package.json
├─ pnpm-lock.yaml
├─ pnpm-workspace.yaml
└─ turbo.json

```