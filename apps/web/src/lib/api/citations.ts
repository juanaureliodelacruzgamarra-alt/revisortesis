"use server";

import { apiFetch, ApiError } from "@/lib/api/client";
import type { Citation } from "@/lib/api/types";

export async function fetchCitations(
  submissionId: string,
  versionId: string,
): Promise<Citation[]> {
  try {
    return await apiFetch<Citation[]>(
      `/api/v1/submissions/${submissionId}/versions/${versionId}/citations`,
    );
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return [];
    throw err;
  }
}
