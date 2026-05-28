"use client";

import { useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { deleteProgramAction } from "@/lib/api/programs";
import { PROGRAM_LEVEL_LABELS, type Program } from "@/lib/api/types";

export function ProgramRow({ program }: { program: Program }) {
  const [pending, start] = useTransition();

  function onDelete() {
    if (!confirm(`¿Eliminar el programa "${program.name}"?`)) return;
    start(async () => {
      await deleteProgramAction(program.id);
    });
  }

  return (
    <li className="flex items-center justify-between gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)]">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{program.code}</Badge>
          <Badge variant="muted">{PROGRAM_LEVEL_LABELS[program.level]}</Badge>
        </div>
        <p className="mt-1 truncate text-sm font-medium" title={program.name}>
          {program.name}
        </p>
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={onDelete}
        disabled={pending}
      >
        {pending ? "Eliminando…" : "Eliminar"}
      </Button>
    </li>
  );
}
