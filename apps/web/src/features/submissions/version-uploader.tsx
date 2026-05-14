"use client";

import { useActionState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  uploadVersionAction,
  type UploadVersionResult,
} from "@/lib/api/submissions";

export function VersionUploader({
  submissionId,
}: {
  submissionId: string;
}) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const boundAction = uploadVersionAction.bind(null, submissionId);
  const [state, formAction, pending] = useActionState<
    UploadVersionResult | null,
    FormData
  >(boundAction, null);

  useEffect(() => {
    if (state?.ok) {
      formRef.current?.reset();
      router.refresh();
    }
  }, [state, router]);

  return (
    <form ref={formRef} action={formAction} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="file">Archivo (.docx o .pdf)</Label>
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

      <div className="space-y-2">
        <Label htmlFor="comment">Comentario (opcional)</Label>
        <Input
          id="comment"
          name="comment"
          placeholder="Cambios respecto a la versión anterior…"
          maxLength={2000}
        />
      </div>

      {state && !state.ok ? (
        <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          {state.error}
        </p>
      ) : null}
      {state?.ok ? (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300">
          Versión {state.version.version_number} subida. Estado:{" "}
          {state.version.parsing_status}
        </p>
      ) : null}

      <Button type="submit" disabled={pending}>
        {pending ? "Subiendo…" : "Subir nueva versión"}
      </Button>
    </form>
  );
}
