"use server";

import { apiFetch } from "@/lib/api/client";

export type StatusCount = { status: string; count: number };
export type ProgramGrade = {
  program_id: string;
  program_code: string;
  program_name: string;
  average_grade: number;
  submissions_count: number;
};
export type StatsOverview = {
  total_submissions: number;
  total_advisors_with_orcid: number;
  submissions_by_status: StatusCount[];
  avg_ai_grade: number | null;
  avg_ai_percentage: number | null;
  ai_human_concordance_pct: number | null;
  plagiarism_alerts: number;
  advisor_fit_alerts: number;
  low_compliance_submissions: number;
  citations_total: number;
  citations_problematic: number;
  grades_per_program: ProgramGrade[];
};
export type ActivityItem = {
  kind: string;
  occurred_at: string;
  submission_id: string;
  submission_title: string;
  actor_name: string;
  description: string;
};

export async function fetchStatsOverview(programId?: string): Promise<StatsOverview> {
  const qs = programId ? `?program_id=${programId}` : "";
  return apiFetch<StatsOverview>(`/api/v1/stats/overview${qs}`);
}

export async function fetchStatsActivity(
  limit = 15,
  programId?: string,
): Promise<ActivityItem[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (programId) params.set("program_id", programId);
  return apiFetch<ActivityItem[]>(`/api/v1/stats/activity?${params.toString()}`);
}
