import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EvaluationSummary } from "@/features/evaluations/evaluation-summary";
import { FindingCard } from "@/features/evaluations/finding-card";
import { SEVERITY_LABELS, type AIEvaluation, type AIFinding, type FindingSeverity } from "@/lib/api/types";

const SEVERITY_ORDER: FindingSeverity[] = ["critical", "major", "minor", "suggestion"];

export function EvaluationPanel({
  evaluation,
  emptyMessage,
  renderFindingExtra,
}: {
  evaluation: AIEvaluation | null;
  emptyMessage: string;
  renderFindingExtra?: (f: AIFinding) => ReactNode;
}) {
  if (!evaluation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Evaluación de IA</CardTitle>
          <CardDescription>{emptyMessage}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const groups = new Map<FindingSeverity, AIFinding[]>();
  for (const sev of SEVERITY_ORDER) groups.set(sev, []);
  for (const f of evaluation.findings) {
    const effective = f.human_severity_override ?? f.severity;
    groups.get(effective)?.push(f);
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Resumen ejecutivo</CardTitle>
          <CardDescription>
            Calificación automatizada KIMY · {evaluation.findings.length}{" "}
            hallazgos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EvaluationSummary evaluation={evaluation} />
        </CardContent>
      </Card>

      {SEVERITY_ORDER.map((sev) => {
        const items = groups.get(sev) ?? [];
        if (items.length === 0) return null;
        return (
          <section key={sev} className="space-y-3">
            <h2 className="flex items-center gap-2 text-base font-semibold">
              <Badge
                variant={
                  sev === "critical"
                    ? "destructive"
                    : sev === "major"
                      ? "warning"
                      : sev === "minor"
                        ? "muted"
                        : "outline"
                }
              >
                {SEVERITY_LABELS[sev]}
              </Badge>
              <span className="text-zinc-500">
                {items.length} hallazgo{items.length === 1 ? "" : "s"}
              </span>
            </h2>
            <div className="space-y-3">
              {items.map((f) => (
                <FindingCard key={f.id} finding={f}>
                  {renderFindingExtra?.(f)}
                </FindingCard>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
