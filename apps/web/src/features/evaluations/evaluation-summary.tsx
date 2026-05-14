import { Badge } from "@/components/ui/badge";
import type { AIEvaluation } from "@/lib/api/types";

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-rose-600 dark:text-rose-400";
}

export function EvaluationSummary({ evaluation }: { evaluation: AIEvaluation }) {
  const scores = [
    { label: "Estructura", value: evaluation.structure_score, weight: 30 },
    { label: "Contenido", value: evaluation.content_score, weight: 40 },
    { label: "Forma", value: evaluation.form_score, weight: 20 },
    { label: "Originalidad", value: evaluation.originality_score, weight: 10 },
  ];

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

      <p className="text-sm text-zinc-700 dark:text-zinc-300">
        {evaluation.executive_summary}
      </p>

      <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
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
          <span className="font-mono font-medium text-zinc-900 dark:text-zinc-100">
            {evaluation.decimal_grade.toFixed(2)} / 20
          </span>
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {scores.map((s) => (
          <div
            key={s.label}
            className="rounded-md border border-zinc-200 p-3 text-center dark:border-zinc-800"
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
