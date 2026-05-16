"use client";

import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { patchFindingAction } from "@/lib/api/evaluations";
import {
  SEVERITY_LABELS,
  type AIFinding,
  type FindingSeverity,
  type HumanAction,
} from "@/lib/api/types";

const SEVERITY_OPTIONS: FindingSeverity[] = [
  "critical",
  "major",
  "minor",
  "suggestion",
];

export function FindingActions({
  submissionId,
  finding,
}: {
  submissionId: string;
  finding: AIFinding;
}) {
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [comment, setComment] = useState(finding.human_comment ?? "");
  const [severity, setSeverity] = useState<FindingSeverity>(
    finding.human_severity_override ?? finding.severity,
  );

  function dispatch(action: HumanAction) {
    setError(null);
    start(async () => {
      const result = await patchFindingAction(
        submissionId,
        finding.id,
        action,
        action === "accepted" ? null : comment,
        action === "modified" ? severity : null,
      );
      if (!result.ok) setError(result.error);
    });
  }

  return (
    <div className="mt-4 space-y-3 border-t border-zinc-200 pt-4 dark:border-[color:rgba(196,181,253,0.12)]">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <Label
            htmlFor={`severity-${finding.id}`}
            className="text-xs uppercase tracking-wide"
          >
            Severidad ajustada (modify)
          </Label>
          <select
            id={`severity-${finding.id}`}
            value={severity}
            onChange={(e) => setSeverity(e.target.value as FindingSeverity)}
            className="flex h-9 w-full rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950 focus-visible:ring-offset-2 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)] dark:focus-visible:ring-violet-500/40"
          >
            {SEVERITY_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {SEVERITY_LABELS[s]}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label
            htmlFor={`comment-${finding.id}`}
            className="text-xs uppercase tracking-wide"
          >
            Comentario (modify / reject)
          </Label>
          <Input
            id={`comment-${finding.id}`}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Justifica tu decisión…"
            maxLength={4000}
          />
        </div>
      </div>

      {error ? (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          onClick={() => dispatch("accepted")}
          disabled={pending}
        >
          Aceptar
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => dispatch("modified")}
          disabled={pending}
        >
          Modificar
        </Button>
        <Button
          type="button"
          size="sm"
          variant="destructive"
          onClick={() => dispatch("rejected")}
          disabled={pending}
        >
          Descartar
        </Button>
      </div>
    </div>
  );
}
