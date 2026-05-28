"use server";

import { apiFetch } from "@/lib/api/client";

export type SubmissionReportRow = {
  submission_id: string;
  program_code: string;
  program_name: string;
  title: string;
  chapter: string | null;
  status: string;
  student_name: string;
  advisor_name: string | null;
  decimal_grade: number | null;
  total_percentage: number | null;
  advisor_fit_score: number | null;
  advisor_fit_alert: boolean;
  latest_version: number;
  created_at: string;
};

export type SubmissionsReport = {
  program_id: string | null;
  status: string | null;
  rows: SubmissionReportRow[];
  total: number;
};

export type ProgramRollupRow = {
  program_id: string;
  program_code: string;
  program_name: string;
  submissions_count: number;
  average_grade: number | null;
  plagiarism_alerts: number;
  fit_alerts: number;
};

export type ProgramsRollup = {
  rows: ProgramRollupRow[];
};

export async function fetchSubmissionsReport(
  filters: { program_id?: string; status?: string } = {},
): Promise<SubmissionsReport> {
  const qs = new URLSearchParams();
  if (filters.program_id) qs.set("program_id", filters.program_id);
  if (filters.status) qs.set("status", filters.status);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<SubmissionsReport>(`/api/v1/reports/submissions${suffix}`);
}

export async function fetchProgramsRollup(): Promise<ProgramsRollup> {
  return apiFetch<ProgramsRollup>("/api/v1/reports/programs");
}
