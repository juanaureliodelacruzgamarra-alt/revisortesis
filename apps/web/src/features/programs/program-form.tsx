"use client";

import { useActionState, useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createProgramAction,
  type CreateProgramResult,
} from "@/lib/api/programs";
import { PROGRAM_LEVEL_LABELS, type ProgramLevel } from "@/lib/api/types";

const LEVELS: ProgramLevel[] = ["undergraduate", "masters", "doctorate"];

export function ProgramForm() {
  const [state, formAction, pending] = useActionState<
    CreateProgramResult | null,
    FormData
  >(createProgramAction, null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state?.ok) formRef.current?.reset();
  }, [state]);

  return (
    <form ref={formRef} action={formAction} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="name">Nombre del programa</Label>
          <Input
            id="name"
            name="name"
            placeholder="Maestría en Ingeniería de Software"
            minLength={2}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="code">Código</Label>
          <Input
            id="code"
            name="code"
            placeholder="MIS"
            minLength={2}
            maxLength={50}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="level">Nivel</Label>
          <select
            id="level"
            name="level"
            defaultValue="masters"
            className="flex h-10 w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950 focus-visible:ring-offset-2 dark:border-zinc-800 dark:bg-zinc-950 dark:focus-visible:ring-zinc-300"
          >
            {LEVELS.map((level) => (
              <option key={level} value={level}>
                {PROGRAM_LEVEL_LABELS[level]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {state && !state.ok ? (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          {state.error}
        </p>
      ) : null}
      {state?.ok ? (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300">
          Programa creado: {state.program.code} — {state.program.name}
        </p>
      ) : null}

      <Button type="submit" disabled={pending}>
        {pending ? "Creando…" : "Crear programa"}
      </Button>
    </form>
  );
}
