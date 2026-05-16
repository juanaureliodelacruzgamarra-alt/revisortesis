"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, extractErrorMessage } from "@/lib/api/client";

export type SystemSetting = {
  key: string;
  value: Record<string, unknown>;
  updated_at: string | null;
  updated_by: string | null;
};

export async function fetchSystemSettings(): Promise<SystemSetting[]> {
  return apiFetch<SystemSetting[]>("/api/v1/admin/settings");
}

export type FineTuningConfigResult =
  | { ok: true; setting: SystemSetting }
  | { ok: false; error: string };

export async function updateFineTuningConfigAction(
  _prev: FineTuningConfigResult | null,
  formData: FormData,
): Promise<FineTuningConfigResult> {
  const min = Number(formData.get("min_examples"));
  if (!Number.isFinite(min) || min < 1 || min > 100_000) {
    return { ok: false, error: "min_examples debe estar entre 1 y 100000." };
  }
  try {
    const setting = await apiFetch<SystemSetting>(
      "/api/v1/admin/settings/fine-tuning",
      { method: "PUT", body: { min_examples: Math.trunc(min) } },
    );
    revalidatePath("/admin/settings");
    revalidatePath("/admin/fine-tuning");
    return { ok: true, setting };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo actualizar la configuración"),
    };
  }
}
