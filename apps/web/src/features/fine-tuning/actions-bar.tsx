"use client";

import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import {
  createFineTuningJobAction,
  refreshJobAction,
  submitJobAction,
  type FineTuningJob,
} from "@/lib/api/fine-tuning";

export function CreateJobButton({
  disabled,
  reason,
}: {
  disabled: boolean;
  reason?: string;
}) {
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function onClick() {
    setError(null);
    start(async () => {
      const result = await createFineTuningJobAction();
      if (!result.ok) setError(result.error);
    });
  }

  return (
    <div className="space-y-2">
      <Button type="button" onClick={onClick} disabled={disabled || pending}>
        {pending ? "Construyendo dataset…" : "Exportar dataset (nuevo job)"}
      </Button>
      {disabled && reason ? (
        <p className="text-xs text-zinc-500">{reason}</p>
      ) : null}
      {error ? (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          {error}
        </p>
      ) : null}
    </div>
  );
}


export function JobActionButtons({
  job,
  openaiAvailable,
}: {
  job: FineTuningJob;
  openaiAvailable: boolean;
}) {
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function submit() {
    setError(null);
    start(async () => {
      const r = await submitJobAction(job.id);
      if (!r.ok) setError(r.error);
    });
  }

  function refresh() {
    setError(null);
    start(async () => {
      const r = await refreshJobAction(job.id);
      if (!r.ok) setError(r.error);
    });
  }

  const canSubmit =
    openaiAvailable && (job.status === "dataset_ready" || job.status === "failed");
  const canRefresh = !!job.openai_job_id;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <a
        href={`/api/fine-tuning/${job.id}/dataset.jsonl`}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs font-medium underline-offset-4 hover:underline"
      >
        Descargar JSONL
      </a>
      {canSubmit ? (
        <Button
          type="button"
          size="sm"
          onClick={submit}
          disabled={pending}
          variant="outline"
        >
          {pending ? "Enviando…" : "Enviar a proveedor"}
        </Button>
      ) : null}
      {canRefresh ? (
        <Button
          type="button"
          size="sm"
          onClick={refresh}
          disabled={pending}
          variant="ghost"
        >
          Refrescar
        </Button>
      ) : null}
      {error ? (
        <span className="text-xs text-rose-600 dark:text-rose-400">{error}</span>
      ) : null}
    </div>
  );
}
