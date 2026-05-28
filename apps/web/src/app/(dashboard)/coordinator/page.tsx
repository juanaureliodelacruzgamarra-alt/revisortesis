import { redirect } from "next/navigation";

import { CoordinatorView } from "@/features/dashboard/coordinator-view";
import { fetchStatsActivity, fetchStatsOverview } from "@/lib/api/stats";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Dashboard · Aurelio" };

export default async function CoordinatorDashboard() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "coordinator" && user.role !== "admin") {
    redirect(`/${user.role}`);
  }

  const [stats, activity] = await Promise.all([
    fetchStatsOverview(),
    fetchStatsActivity(15),
  ]);

  return (
    <CoordinatorView
      totalSubmissions={stats.total_submissions}
      avgAiGrade={stats.avg_ai_grade}
      avgAiPercentage={stats.avg_ai_percentage}
      aiHumanConcordance={stats.ai_human_concordance_pct}
      advisorsWithOrcid={stats.total_advisors_with_orcid}
      plagiarismAlerts={stats.plagiarism_alerts}
      advisorFitAlerts={stats.advisor_fit_alerts}
      lowCompliance={stats.low_compliance_submissions}
      citationsProblematic={stats.citations_problematic}
      citationsTotal={stats.citations_total}
      submissionsByStatus={stats.submissions_by_status}
      gradesPerProgram={stats.grades_per_program}
      activity={activity}
    />
  );
}
