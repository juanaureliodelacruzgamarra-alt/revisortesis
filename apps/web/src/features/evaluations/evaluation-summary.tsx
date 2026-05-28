import { Badge } from "@/components/ui/badge";
import type { AIEvaluation } from "@/lib/api/types";

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-rose-600 dark:text-rose-400";
}

function aiDetectionColor(pct: number): string {
  if (pct >= 60) return "text-rose-600 dark:text-rose-400";
  if (pct >= 30) return "text-amber-600 dark:text-amber-400";
  return "text-emerald-600 dark:text-emerald-400";
}

function hashSeed(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) {
    h = (h * 31 + id.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function estimatedAIPercent(evaluation: AIEvaluation): number {
  const base = Math.max(0, Math.min(100, 100 - evaluation.originality_score));
  const jitter = (hashSeed(evaluation.id) % 13) - 6;
  return Math.max(0, Math.min(100, base + jitter));
}

function copyleaksScanId(id: string): string {
  const seed = hashSeed(id).toString(16).toUpperCase().padStart(8, "0");
  return `CL-${seed.slice(0, 4)}-${seed.slice(4, 8)}`;
}

export function EvaluationSummary({ evaluation }: { evaluation: AIEvaluation }) {
  const scores = [
    { label: "Estructura", value: evaluation.structure_score, weight: 30 },
    { label: "Contenido", value: evaluation.content_score, weight: 40 },
    { label: "Forma", value: evaluation.form_score, weight: 20 },
    { label: "Originalidad", value: evaluation.originality_score, weight: 10 },
  ];

  const aiPct = estimatedAIPercent(evaluation);
  const humanPct = 100 - aiPct;
  const scanId = copyleaksScanId(evaluation.id);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
        <Badge variant={evaluation.backend === "stub" ? "muted" : "default"}>
          {evaluation.backend}
        </Badge>
        <span className="font-mono">{evaluation.model}</span>
        <span>·</span>
        <span>prompt {evaluation.prompt_version}</span>
        <span>·</span>
        <span>{evaluation.duration_ms} ms</span>
      </div>

      <p className="text-sm text-zinc-700 dark:text-[color:var(--aurora-cream-dim)]">
        {evaluation.executive_summary}
      </p>

      <div className="rounded-lg border border-zinc-200 p-4 dark:border-[color:rgba(196,181,253,0.12)]">
        <div className="flex items-baseline justify-between">
          <span className="text-sm font-medium text-zinc-500">
            Cumplimiento total
          </span>
          <span className={`text-3xl font-semibold ${scoreColor(evaluation.total_percentage)}`}>
            {evaluation.total_percentage.toFixed(1)}%
          </span>
        </div>
        <div className="mt-1 text-sm text-zinc-500">
          Nota:{" "}
          <span className="font-mono font-medium text-zinc-900 dark:text-[color:var(--aurora-cream)]">
            {evaluation.decimal_grade.toFixed(2)} / 20
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-gradient-to-br from-white to-zinc-50 p-4 dark:border-[color:rgba(196,181,253,0.12)] dark:from-[color:rgba(30,27,45,0.6)] dark:to-[color:rgba(30,27,45,0.3)]">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-[#0ea5e9] text-[10px] font-bold text-white">
              CL
            </span>
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-zinc-800 dark:text-[color:var(--aurora-cream)]">
                Copyleaks AI Detector
              </span>
              <span className="text-[10px] uppercase tracking-wide text-zinc-400">
                Scan {scanId}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <Badge variant="muted">v4.2</Badge>
            <span className="inline-flex items-center rounded-md border border-amber-400 bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:border-amber-500 dark:bg-amber-900/40 dark:text-amber-300">
              DEMO
            </span>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs uppercase tracking-wide text-zinc-500">
              AI Content
            </div>
            <div className={`mt-1 text-3xl font-semibold ${aiDetectionColor(aiPct)}`}>
              {aiPct.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-zinc-500">
              Human Content
            </div>
            <div className="mt-1 text-3xl font-semibold text-zinc-700 dark:text-[color:var(--aurora-cream-dim)]">
              {humanPct.toFixed(1)}%
            </div>
          </div>
        </div>

        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-[color:rgba(196,181,253,0.12)]">
          <div
            className="h-full bg-gradient-to-r from-rose-500 to-amber-500"
            style={{ width: `${aiPct}%` }}
          />
        </div>

        <p className="mt-2 text-[10px] leading-snug text-amber-600 dark:text-amber-400">
          Vista de demostración. Valor estimado a partir del puntaje de originalidad; no proviene de una integración real con Copyleaks.
        </p>
      </div>

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {scores.map((s) => (
          <div
            key={s.label}
            className="rounded-md border border-zinc-200 p-3 text-center dark:border-[color:rgba(196,181,253,0.12)]"
          >
            <dt className="text-xs uppercase tracking-wide text-zinc-500">
              {s.label}
            </dt>
            <dd className={`mt-1 text-xl font-semibold ${scoreColor(s.value)}`}>
              {s.value.toFixed(0)}
            </dd>
            <dd className="text-xs text-zinc-400">peso {s.weight}%</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
