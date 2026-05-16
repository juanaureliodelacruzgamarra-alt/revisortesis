"use client";

import { useActionState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createSubmissionAction,
  type CreateSubmissionResult,
} from "@/lib/api/submissions";
import { PROGRAM_LEVEL_LABELS, type Program } from "@/lib/api/types";

export function SubmissionForm({ programs }: { programs: Program[] }) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const [state, formAction, pending] = useActionState<
    CreateSubmissionResult | null,
    FormData
  >(createSubmissionAction, null);

  useEffect(() => {
    if (state?.ok) {
      formRef.current?.reset();
      router.push(`/student/submissions/${state.submission.id}`);
    }
  }, [state, router]);

  if (programs.length === 0) {
    return (
      <p className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
        Aún no hay programas registrados. Contacta al administrador para que cree
        tu programa antes de poder subir avances.
      </p>
    );
  }

  return (
    <form ref={formRef} action={formAction} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="program_id">Programa académico</Label>
        <select
          id="program_id"
          name="program_id"
          required
          defaultValue={programs[0]?.id}
          className="flex h-10 w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950 focus-visible:ring-offset-2 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)] dark:focus-visible:ring-violet-500/40"
        >
          {programs.map((p) => (
            <option key={p.id} value={p.id}>
              [{p.code}] {p.name} — {PROGRAM_LEVEL_LABELS[p.level]}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="title">Título del avance</Label>
        <Input
          id="title"
          name="title"
          placeholder="Avance del Capítulo 1"
          minLength={2}
          maxLength={255}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="chapter">Capítulo (opcional)</Label>
        <Input
          id="chapter"
          name="chapter"
          placeholder="Capítulo 1, Tesis completa, etc."
          maxLength={100}
        />
      </div>

      {state && !state.ok ? (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          {state.error}
        </p>
      ) : null}

      <Button type="submit" disabled={pending}>
        {pending ? "Creando…" : "Crear avance"}
      </Button>
    </form>
  );
}
