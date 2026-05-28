"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, extractErrorMessage } from "@/lib/api/client";
import type {
  SubmissionDetail,
  SubmissionSummary,
  SubmissionVersionDetail,
} from "@/lib/api/types";

export type SubmissionFilters = {
  program_id?: string;
  status?: string;
  advisor_id?: string;
  fit_alert?: boolean;
};

export async function fetchSubmissions(
  filters: SubmissionFilters = {},
): Promise<SubmissionSummary[]> {
  const qs = new URLSearchParams();
  if (filters.program_id) qs.set("program_id", filters.program_id);
  if (filters.status) qs.set("status", filters.status);
  if (filters.advisor_id) qs.set("advisor_id", filters.advisor_id);
  if (filters.fit_alert !== undefined) qs.set("fit_alert", String(filters.fit_alert));
  const path = qs.toString()
    ? `/api/v1/submissions?${qs.toString()}`
    : "/api/v1/submissions";
  return apiFetch<SubmissionSummary[]>(path);
}

export type AdvisorOption = {
  id: string;
  full_name: string;
  email: string;
  orcid_id: string | null;
  orcid_linked: boolean;
};

export async function fetchEligibleAdvisors(): Promise<AdvisorOption[]> {
  return apiFetch<AdvisorOption[]>("/api/v1/submissions/advisors");
}

export async function assignAdvisorAction(
  submissionId: string,
  advisorId: string | null,
): Promise<void> {
  await apiFetch(`/api/v1/submissions/${submissionId}/advisor`, {
    method: "PATCH",
    body: { advisor_id: advisorId },
  });
  revalidatePath("/coordinator/submissions");
  revalidatePath("/coordinator");
}

// ---- Bulk ----

export type BulkOperation = "reprocess_ai" | "set_status" | "assign_advisor";

export type BulkOutcome = {
  submission_id: string;
  ok: boolean;
  detail: string;
};

export type BulkResponse = {
  operation: string;
  total: number;
  succeeded: number;
  failed: number;
  outcomes: BulkOutcome[];
};

export type BulkPayload = {
  operation: BulkOperation;
  submission_ids: string[];
  status?: string | null;
  advisor_id?: string | null;
};

export async function bulkApplyAction(payload: BulkPayload): Promise<BulkResponse> {
  const result = await apiFetch<BulkResponse>("/api/v1/submissions/bulk", {
    method: "POST",
    body: payload,
  });
  revalidatePath("/coordinator/submissions");
  revalidatePath("/coordinator");
  return result;
}

// Used by the polling progress UI — fetches just the latest_version_status of
// the given IDs.
export async function fetchSubmissionStatusMap(
  ids: string[],
): Promise<Record<string, string | null>> {
  if (ids.length === 0) return {};
  const all = await fetchSubmissions();
  const wanted = new Set(ids);
  const out: Record<string, string | null> = {};
  for (const s of all) {
    if (wanted.has(s.id)) out[s.id] = s.latest_version_status ?? null;
  }
  return out;
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
