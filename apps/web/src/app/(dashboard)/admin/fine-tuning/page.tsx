import { redirect } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { KpiCard } from "@/features/dashboard/kpi-card";
import {
  CreateJobButton,
  JobActionButtons,
} from "@/features/fine-tuning/actions-bar";
import { ModelToggle } from "@/features/fine-tuning/model-toggle";
import {
  fetchFineTuningJobs,
  fetchFineTuningStats,
  fetchModelPreference,
  type FineTuningStatus,
} from "@/lib/api/fine-tuning";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Fine-tuning · Aurelio" };

function statusVariant(s: FineTuningStatus) {
  switch (s) {
    case "succeeded":
      return "success" as const;
    case "failed":
    case "cancelled":
      return "destructive" as const;
    case "running":
    case "queued":
    case "uploading":
      return "warning" as const;
    case "dataset_ready":
      return "muted" as const;
  }
}

export default async function FineTuningPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "admin") redirect(`/${user.role}`);

  const [stats, jobs, pref] = await Promise.all([
    fetchFineTuningStats(),
    fetchFineTuningJobs(),
    fetchModelPreference(),
  ]);

  const exportReason = !stats.ready_to_export
    ? "Aún no hay feedback humano elegible. Cuando los asesores modifiquen o descarten hallazgos, podrás exportar el dataset."
    : undefined;

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Administrador
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Fine-tuning</h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Exporta el feedback humano acumulado como dataset JSONL. Con Gemini el
          envío programático no está cableado (vive en Vertex AI / Gemini
          Tuning); el dataset siempre se puede descargar para auditoría o
          entrenamiento offline.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          label="Ejemplos elegibles"
          value={stats.total_eligible}
          helper={`umbral sugerido: ${stats.min_examples_threshold}`}
        />
        <KpiCard
          label="Modificados"
          value={stats.by_action.modified ?? 0}
        />
        <KpiCard
          label="Descartados"
          value={stats.by_action.rejected ?? 0}
        />
        <KpiCard
          label="Tuning programático"
          value={stats.provider_available ? "Disponible" : "No disponible"}
          tone={stats.provider_available ? "success" : "warning"}
          helper="Con Gemini se exporta el JSONL para entrenar offline"
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Nuevo job de fine-tuning</CardTitle>
          <CardDescription>
            Construye un snapshot del dataset con los hallazgos modificados,
            descartados y con severidad ajustada. Cada job genera su propio
            archivo JSONL inmutable.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <CreateJobButton
            disabled={!stats.ready_to_export}
            reason={exportReason}
          />
          {!stats.ready_to_submit && stats.provider_available ? (
            <p className="text-xs text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
              Estás bajo el umbral sugerido ({stats.total_eligible}/
              {stats.min_examples_threshold}). Puedes exportar igualmente, pero
              el proveedor puede rechazar datasets muy pequeños.
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Jobs registrados ({jobs.length})</CardTitle>
          <CardDescription>
            Cada job conserva su JSONL en disco. Con Gemini no se envía
            automáticamente — descarga el archivo para entrenar en Vertex AI.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <p className="text-sm text-zinc-500">
              Aún no hay jobs. Crea el primero desde el botón de arriba.
            </p>
          ) : (
            <ul className="space-y-3">
              {jobs.map((j) => (
                <li
                  key={j.id}
                  className="rounded-md border border-zinc-200 p-3 text-sm dark:border-[color:rgba(196,181,253,0.12)]"
                >
                  <div className="flex flex-wrap items-baseline gap-2">
                    <Badge variant={statusVariant(j.status)}>{j.status}</Badge>
                    <Badge variant="muted">{j.examples_count} ejemplos</Badge>
                    <span className="font-mono text-xs text-zinc-500">
                      base {j.base_model}
                    </span>
                    {j.openai_job_id ? (
                      <span className="font-mono text-xs text-zinc-500">
                        job {j.openai_job_id}
                      </span>
                    ) : null}
                    {j.fine_tuned_model ? (
                      <Badge variant="success">
                        Modelo: {j.fine_tuned_model}
                      </Badge>
                    ) : null}
                  </div>
                  {j.error ? (
                    <p className="mt-1 text-xs text-rose-600 dark:text-rose-400">
                      {j.error}
                    </p>
                  ) : null}
                  <p className="mt-1 text-xs text-zinc-500">
                    Creado{" "}
                    {new Date(j.created_at).toLocaleString("es-PE")}
                    {j.submitted_at
                      ? ` · enviado ${new Date(j.submitted_at).toLocaleString("es-PE")}`
                      : ""}
                    {j.finished_at
                      ? ` · terminado ${new Date(j.finished_at).toLocaleString("es-PE")}`
                      : ""}
                  </p>
                  <div className="mt-2">
                    <JobActionButtons
                      job={j}
                      openaiAvailable={stats.provider_available}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Modelo activo (A/B)</CardTitle>
          <CardDescription>
            Toggle entre el modelo Gemini base y un modelo fine-tuneado para
            todas las evaluaciones IA nuevas. El stub heurístico sigue siendo el
            fallback si no hay GEMINI_API_KEY configurada.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ModelToggle pref={pref} />
        </CardContent>
      </Card>
    </div>
  );
}
