"use client";

import { useActionState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  updateFineTuningConfigAction,
  type FineTuningConfigResult,
} from "@/lib/api/settings";

export function FtThresholdForm({ minExamples }: { minExamples: number }) {
  const [state, formAction, pending] = useActionState<
    FineTuningConfigResult | null,
    FormData
  >(updateFineTuningConfigAction, null);

  return (
    <form action={formAction} className="space-y-3">
      <div className="space-y-1">
        <Label htmlFor="min_examples">Mínimo de ejemplos para entrenar</Label>
        <Input
          id="min_examples"
          name="min_examples"
          type="number"
          min={1}
          max={100000}
          defaultValue={minExamples}
          required
        />
        <p className="text-xs text-zinc-500">
          Umbral mínimo de feedback humano (acciones &ldquo;modificado&rdquo; o
          &ldquo;descartado&rdquo;) antes de habilitar el envío del dataset a OpenAI.
        </p>
      </div>

      {state && !state.ok ? (
        <p className="text-xs text-rose-600 dark:text-rose-400">{state.error}</p>
      ) : null}
      {state?.ok ? (
        <p className="text-xs text-emerald-600 dark:text-emerald-400">
          Guardado.
        </p>
      ) : null}

      <Button type="submit" disabled={pending}>
        {pending ? "Guardando…" : "Guardar umbral"}
      </Button>
    </form>
  );
}
