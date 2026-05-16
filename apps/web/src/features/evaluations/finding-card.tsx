import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import {
  FINDING_TYPE_LABELS,
  HUMAN_ACTION_LABELS,
  SEVERITY_LABELS,
  type AIFinding,
  type FindingSeverity,
} from "@/lib/api/types";

function severityVariant(s: FindingSeverity) {
  switch (s) {
    case "critical":
      return "destructive" as const;
    case "major":
      return "warning" as const;
    case "minor":
      return "muted" as const;
    case "suggestion":
      return "outline" as const;
  }
}

export function FindingCard({
  finding,
  children,
}: {
  finding: AIFinding;
  children?: ReactNode;
}) {
  const effectiveSeverity =
    finding.human_severity_override ?? finding.severity;

  return (
    <article className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)]">
      <header className="flex flex-wrap items-center gap-2">
        <Badge variant={severityVariant(effectiveSeverity)}>
          {SEVERITY_LABELS[effectiveSeverity]}
        </Badge>
        <Badge variant="outline">{FINDING_TYPE_LABELS[finding.type]}</Badge>
        {finding.section ? (
          <span className="text-xs font-medium text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
            {finding.section}
          </span>
        ) : null}
        {finding.human_action ? (
          <Badge
            variant={
              finding.human_action === "accepted"
                ? "success"
                : finding.human_action === "rejected"
                  ? "destructive"
                  : "default"
            }
            className="ml-auto"
          >
            {HUMAN_ACTION_LABELS[finding.human_action]}
          </Badge>
        ) : null}
      </header>

      <p className="mt-3 text-sm text-zinc-900 dark:text-[color:var(--aurora-cream)]">
        {finding.description}
      </p>

      {finding.instruction ? (
        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Cómo corregir
          </p>
          <p className="mt-1 text-sm text-zinc-700 dark:text-[color:var(--aurora-cream-dim)]">
            {finding.instruction}
          </p>
        </div>
      ) : null}

      {finding.example ? (
        <div className="mt-3 rounded-md bg-zinc-50 p-3 text-sm italic text-zinc-700 dark:bg-[rgba(20,22,62,0.55)]/60 dark:text-[color:var(--aurora-cream-dim)]">
          <span className="not-italic text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Ejemplo
          </span>
          <p className="mt-1">{finding.example}</p>
        </div>
      ) : null}

      {finding.recommendation ? (
        <p className="mt-3 text-sm text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          <span className="font-medium">Recomendación:</span>{" "}
          {finding.recommendation}
        </p>
      ) : null}

      {finding.human_comment ? (
        <div className="mt-3 rounded-md border-l-4 border-zinc-300 bg-zinc-50 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-[rgba(20,22,62,0.55)]/60">
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Nota del asesor
          </p>
          <p className="mt-1 text-zinc-700 dark:text-[color:var(--aurora-cream-dim)]">
            {finding.human_comment}
          </p>
        </div>
      ) : null}

      {children}
    </article>
  );
}
