"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, extractErrorMessage } from "@/lib/api/client";

export type FineTuningStats = {
  total_eligible: number;
  by_action: Record<string, number>;
  by_severity: Record<string, number>;
  min_examples_threshold: number;
  ready_to_export: boolean;
  ready_to_submit: boolean;
  provider_available: boolean;
};

export type FineTuningStatus =
  | "dataset_ready"
  | "uploading"
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export type FineTuningJob = {
  id: string;
  status: FineTuningStatus;
  examples_count: number;
  base_model: string;
  openai_file_id: string | null;
  openai_job_id: string | null;
  fine_tuned_model: string | null;
  error: string | null;
  dataset_path: string;
  submitted_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type ModelPreference = {
  provider: string;
  model: string;
  fine_tuned_model: string | null;
  use_fine_tuned: boolean;
};

export async function fetchFineTuningStats(): Promise<FineTuningStats> {
  return apiFetch<FineTuningStats>("/api/v1/admin/fine-tuning/stats");
}

export async function fetchFineTuningJobs(): Promise<FineTuningJob[]> {
  return apiFetch<FineTuningJob[]>("/api/v1/admin/fine-tuning/jobs");
}

export async function fetchModelPreference(): Promise<ModelPreference> {
  return apiFetch<ModelPreference>("/api/v1/admin/settings/ai-model");
}

export type CreateJobResult =
  | { ok: true; job: FineTuningJob }
  | { ok: false; error: string };

export async function createFineTuningJobAction(): Promise<CreateJobResult> {
  try {
    const job = await apiFetch<FineTuningJob>("/api/v1/admin/fine-tuning/jobs", {
      method: "POST",
    });
    revalidatePath("/admin/fine-tuning");
    return { ok: true, job };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo construir el dataset"),
    };
  }
}

export async function submitJobAction(
  jobId: string,
): Promise<CreateJobResult> {
  try {
    const job = await apiFetch<FineTuningJob>(
      `/api/v1/admin/fine-tuning/jobs/${jobId}/submit`,
      { method: "POST" },
    );
    revalidatePath("/admin/fine-tuning");
    return { ok: true, job };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo enviar el dataset"),
    };
  }
}

export async function refreshJobAction(
  jobId: string,
): Promise<CreateJobResult> {
  try {
    const job = await apiFetch<FineTuningJob>(
      `/api/v1/admin/fine-tuning/jobs/${jobId}/refresh`,
      { method: "POST" },
    );
    revalidatePath("/admin/fine-tuning");
    return { ok: true, job };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo refrescar el estado"),
    };
  }
}

export type UpdateModelResult =
  | { ok: true; pref: ModelPreference }
  | { ok: false; error: string };

export async function updateModelPreferenceAction(
  patch: Partial<ModelPreference>,
): Promise<UpdateModelResult> {
  try {
    const pref = await apiFetch<ModelPreference>(
      "/api/v1/admin/settings/ai-model",
      { method: "PUT", body: patch },
    );
    revalidatePath("/admin/fine-tuning");
    revalidatePath("/admin/settings");
    revalidatePath("/admin");
    return { ok: true, pref };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo actualizar el modelo activo"),
    };
  }
}
