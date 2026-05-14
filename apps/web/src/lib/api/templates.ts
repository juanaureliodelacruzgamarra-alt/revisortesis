"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, extractErrorMessage } from "@/lib/api/client";
import type { TemplateDetail, TemplateSummary } from "@/lib/api/types";

export async function fetchTemplates(
  programId?: string,
): Promise<TemplateSummary[]> {
  const qs = programId ? `?program_id=${programId}` : "";
  return apiFetch<TemplateSummary[]>(`/api/v1/templates${qs}`);
}

export async function fetchTemplate(id: string): Promise<TemplateDetail> {
  return apiFetch<TemplateDetail>(`/api/v1/templates/${id}`);
}

export type UploadTemplateResult =
  | { ok: true; template: TemplateDetail }
  | { ok: false; error: string };

export async function uploadTemplateAction(
  _prev: UploadTemplateResult | null,
  formData: FormData,
): Promise<UploadTemplateResult> {
  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return { ok: false, error: "Selecciona un archivo Word o PDF" };
  }
  const programId = String(formData.get("program_id") ?? "");
  const title = String(formData.get("title") ?? "").trim();
  if (!programId || !title) {
    return { ok: false, error: "Programa y título son requeridos" };
  }

  try {
    const template = await apiFetch<TemplateDetail>("/api/v1/templates", {
      method: "POST",
      formData,
    });
    revalidatePath("/coordinator/templates");
    return { ok: true, template };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo subir la plantilla"),
    };
  }
}

export async function activateTemplateAction(id: string): Promise<void> {
  await apiFetch(`/api/v1/templates/${id}/activate`, { method: "POST" });
  revalidatePath("/coordinator/templates");
  revalidatePath(`/coordinator/templates/${id}`);
}

export async function deleteTemplateAction(id: string): Promise<void> {
  await apiFetch(`/api/v1/templates/${id}`, { method: "DELETE" });
  revalidatePath("/coordinator/templates");
}
