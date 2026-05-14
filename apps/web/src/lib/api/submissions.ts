"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, extractErrorMessage } from "@/lib/api/client";
import type {
  SubmissionDetail,
  SubmissionSummary,
  SubmissionVersionDetail,
} from "@/lib/api/types";

export async function fetchSubmissions(): Promise<SubmissionSummary[]> {
  return apiFetch<SubmissionSummary[]>("/api/v1/submissions");
}

export async function fetchSubmission(id: string): Promise<SubmissionDetail> {
  return apiFetch<SubmissionDetail>(`/api/v1/submissions/${id}`);
}

export type CreateSubmissionResult =
  | { ok: true; submission: SubmissionDetail }
  | { ok: false; error: string };

export async function createSubmissionAction(
  _prev: CreateSubmissionResult | null,
  formData: FormData,
): Promise<CreateSubmissionResult> {
  const program_id = String(formData.get("program_id") ?? "");
  const title = String(formData.get("title") ?? "").trim();
  const chapter = String(formData.get("chapter") ?? "").trim() || null;
  if (!program_id || !title) {
    return { ok: false, error: "Programa y título son requeridos" };
  }
  try {
    const submission = await apiFetch<SubmissionDetail>(
      "/api/v1/submissions",
      {
        method: "POST",
        body: { program_id, title, chapter },
      },
    );
    revalidatePath("/student/submissions");
    return { ok: true, submission };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo crear el avance"),
    };
  }
}

export type UploadVersionResult =
  | { ok: true; version: SubmissionVersionDetail }
  | { ok: false; error: string };

export async function uploadVersionAction(
  submissionId: string,
  _prev: UploadVersionResult | null,
  formData: FormData,
): Promise<UploadVersionResult> {
  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return { ok: false, error: "Selecciona un archivo Word o PDF" };
  }
  try {
    const version = await apiFetch<SubmissionVersionDetail>(
      `/api/v1/submissions/${submissionId}/versions`,
      { method: "POST", formData },
    );
    revalidatePath("/student/submissions");
    revalidatePath(`/student/submissions/${submissionId}`);
    return { ok: true, version };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo subir la versión"),
    };
  }
}
