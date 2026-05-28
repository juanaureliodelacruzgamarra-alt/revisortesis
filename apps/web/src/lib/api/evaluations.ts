"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError, extractErrorMessage } from "@/lib/api/client";
import type {
  AIEvaluation,
  AIFinding,
  FindingSeverity,
  HumanAction,
} from "@/lib/api/types";

export async function fetchEvaluation(
  submissionId: string,
  versionId: string,
): Promise<AIEvaluation | null> {
  try {
    return await apiFetch<AIEvaluation>(
      `/api/v1/submissions/${submissionId}/versions/${versionId}/evaluation`,
    );
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export type FindingPatchResult =
  | { ok: true; finding: AIFinding }
  | { ok: false; error: string };

export async function patchFindingAction(
  submissionId: string,
  findingId: string,
  action: HumanAction,
  comment: string | null,
  severityOverride: FindingSeverity | null,
): Promise<FindingPatchResult> {
  try {
    const finding = await apiFetch<AIFinding>(`/api/v1/findings/${findingId}`, {
      method: "PATCH",
      body: {
        action,
        comment: comment && comment.trim() ? comment.trim() : null,
        severity_override: severityOverride,
      },
    });
    revalidatePath(`/advisor/reviews/${submissionId}`);
    revalidatePath(`/student/submissions/${submissionId}`);
    return { ok: true, finding };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo guardar la acción"),
    };
  }
}
