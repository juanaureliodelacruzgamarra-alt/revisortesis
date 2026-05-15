# Fine-tuning pipeline (Fase 10)

Este documento describe cómo KIMY transforma el feedback humano sobre los hallazgos de IA en un dataset listo para fine-tuning de `gpt-4o-mini`, cómo enviarlo a OpenAI y cómo activar el modelo resultante en el sistema.

## Qué se exporta

Sólo `ai_findings` donde el asesor **realmente cambió** algo:

| Acción humana | ¿Entra al dataset? | Ejemplo "assistant" |
|---|---|---|
| `accepted` sin `human_severity_override` | No (el modelo ya acertó) | — |
| `accepted` **con** `human_severity_override` | Sí | `{"action":"keep","severity":<nueva>,…}` |
| `modified` | Sí (el `human_comment` se vuelve la descripción canónica) | `{"action":"keep",…}` |
| `rejected` | Sí (ejemplo negativo) | `{"action":"reject","reason":<comment>}` |

Filtro adicional: `reviewed_at IS NOT NULL` para evitar registros incompletos.

## Formato del JSONL

Cada línea es un objeto al formato **Chat fine-tuning** de OpenAI:

```jsonc
{"messages": [
  {"role": "system", "content": "Eres KIMY, un evaluador académico…"},
  {"role": "user",   "content": "# Avance: …\nSección: …\n…"},
  {"role": "assistant", "content": "{\"action\":\"keep\",\"severity\":\"major\",\"description\":\"…\",\"instruction\":\"…\"}"}
]}
```

El system prompt es estable (versionado en `services/fine_tuning/exporter.py::_SYSTEM_PROMPT`). El user prompt se reconstruye desde la fila de `ai_findings` — más compacto que volcar el contexto LLM original, pero suficiente para capturar la decisión de severidad y la reescritura.

## Endpoints (admin only)

| Método | Path | Para qué |
|---|---|---|
| `GET` | `/api/v1/admin/fine-tuning/stats` | Contadores + umbral + disponibilidad OpenAI |
| `POST` | `/api/v1/admin/fine-tuning/jobs` | Construye un job nuevo (snapshot del dataset, estado `dataset_ready`) |
| `GET` | `/api/v1/admin/fine-tuning/jobs` | Listado de jobs |
| `GET` | `/api/v1/admin/fine-tuning/jobs/{id}/dataset.jsonl` | Descarga el JSONL |
| `POST` | `/api/v1/admin/fine-tuning/jobs/{id}/submit` | Sube el JSONL a OpenAI y crea el FT job |
| `POST` | `/api/v1/admin/fine-tuning/jobs/{id}/refresh` | Refresca status desde OpenAI |
| `GET` | `/api/v1/admin/settings/ai-model` | Preferencia actual del modelo |
| `PUT` | `/api/v1/admin/settings/ai-model` | Toggle base/fine-tuneado |

Todos requieren rol `admin`.

## Flujo manual con la API de OpenAI

Si quieres bypasear el botón de la UI y trabajar contra OpenAI directamente:

```bash
# 1. Descarga el JSONL del job que creaste por la UI
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://localhost:8005/api/v1/admin/fine-tuning/jobs/<JOB_ID>/dataset.jsonl \
  -o ft.jsonl

# 2. Súbelo a OpenAI Files API
openai api files.create --file ft.jsonl --purpose fine-tune

# 3. Crea el job de fine-tuning
openai api fine_tuning.jobs.create \
  --training_file <FILE_ID> \
  --model gpt-4o-mini-2024-07-18

# 4. Poll del estado
openai api fine_tuning.jobs.retrieve --id <FT_JOB_ID>

# 5. Cuando termine en `succeeded`, copia el `fine_tuned_model` (ej.
#    ft:gpt-4o-mini-2024-07-18:org-id:slug:abc123) y pégalo en
#    /admin/fine-tuning desde la UI, activando "Usar modelo fine-tuneado".
```

## Activación del modelo (A/B)

El admin define en `system_settings` el modelo activo:

```jsonc
// key = "ai.model_preference"
{
  "openai_model":     "gpt-4o-mini",
  "fine_tuned_model": "ft:gpt-4o-mini-…",   // null si aún no hay
  "use_fine_tuned":   true                  // toggle A/B
}
```

El pipeline (`services/ai/pipeline.py::_run_inner`) lee este valor antes de cada evaluación y le pasa el ID al `llm_evaluator` vía `openai_model_override`. No requiere reinicio.

El stub heurístico determinístico sigue siendo el fallback cuando no hay key configurada — el toggle sólo afecta a las llamadas LLM reales.

## Calidad y tamaño mínimo

OpenAI rechaza datasets con < 10 ejemplos. Idealmente queremos ≥ 100 para que el fine-tuning aporte señal. KIMY define un umbral configurable (`system_settings/ai.fine_tuning.min_examples`, default 500) que sólo afecta la UI: bloquea el botón "Enviar a OpenAI" hasta superarlo. **No se envía automáticamente** — un humano siempre toma esa decisión.

## Auditoría

Cada job conserva:
- `dataset_path`: archivo JSONL inmutable en `storage/fine-tuning/<uuid>.jsonl`
- `examples_count`: cuántas filas del feedback acumulado entraron
- `submitted_at` / `finished_at`: trazabilidad temporal
- `openai_file_id` y `openai_job_id`: para correlacionar con la consola de OpenAI

Esto permite reproducir un job antiguo sin depender de que `ai_findings` esté congelado.

## Estados del job

```
dataset_ready  →  uploading  →  queued  →  running  →  succeeded
                                                  └→  failed
                                                  └→  cancelled
```

`failed` se puede reenviar; el resto son terminales.

## Limitaciones conocidas

- **No retraining automático**: el pipeline lee `fine_tuned_model` pero no entrena solo. El operador decide cuándo (y si) ejecutar el FT, para controlar costos.
- **Datasets pequeños**: OpenAI puede rechazar < 10 ejemplos. El error vuelve en `FineTuningJob.error`.
- **Sin clasificador local**: el brief menciona una alternativa con scikit-learn para severidad. No está implementada — el dataset se puede usar offline si se necesita.
