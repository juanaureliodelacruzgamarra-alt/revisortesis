"use client";

import { useActionState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  uploadTemplateAction,
  type UploadTemplateResult,
} from "@/lib/api/templates";
import type { Program } from "@/lib/api/types";
import { PROGRAM_LEVEL_LABELS } from "@/lib/api/types";

export function TemplateForm({ programs }: { programs: Program[] }) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const [state, formAction, pending] = useActionState<
    UploadTemplateResult | null,
    FormData
  >(uploadTemplateAction, null);

  useEffect(() => {
    if (state?.ok) {
      formRef.current?.reset();
      router.push(`/coordinator/templates/${state.template.id}`);
    }
  }, [state, router]);

  if (programs.length === 0) {
    return (
      <p className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
        Aún no hay programas académicos creados. Pide al administrador que cree
        al menos uno antes de subir documentos patrón.
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
        <Label htmlFor="title">Título de la plantilla</Label>
        <Input
          id="title"
          name="title"
          placeholder="Plantilla MIS v1"
          minLength={2}
          maxLength={255}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Descripción (opcional)</Label>
        <Input
          id="description"
          name="description"
          placeholder="Estructura institucional para tesis de maestría"
          maxLength={2000}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="file">Documento (Word .docx o PDF)</Label>
        <input
          id="file"
          name="file"
          type="file"
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.pdf,application/pdf"
          required
          className="block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:bg-zinc-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-zinc-50 hover:file:bg-zinc-900/90 dark:file:bg-zinc-50 dark:file:text-zinc-900"
        />
        <p className="text-xs text-zinc-500">Máximo 50 MB.</p>
      </div>

      {state && !state.ok ? (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          {state.error}
        </p>
      ) : null}

      <Button type="submit" disabled={pending}>
        {pending ? "Subiendo…" : "Subir y analizar"}
      </Button>
    </form>
  );
}
