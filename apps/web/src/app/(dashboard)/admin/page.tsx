import { redirect } from "next/navigation";

import { AdminView } from "@/features/dashboard/admin-view";
import { fetchFineTuningStats, fetchModelPreference } from "@/lib/api/fine-tuning";
import { fetchPrograms } from "@/lib/api/programs";
import { fetchStatsOverview } from "@/lib/api/stats";
import { fetchAdminUsers } from "@/lib/api/users";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Administrador · Aurelio" };

export default async function AdminHome() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "admin") redirect(`/${user.role}`);

  const [overview, users, programs, ftStats, pref] = await Promise.all([
    fetchStatsOverview(),
    fetchAdminUsers({ limit: 500 }),
    fetchPrograms(),
    fetchFineTuningStats(),
    fetchModelPreference(),
  ]);

  const totalUsers = users.length;
  const usersByRole = users.reduce<Record<string, number>>((acc, u) => {
    acc[u.role] = (acc[u.role] ?? 0) + 1;
    return acc;
  }, {});

  const activeModel =
    pref.use_fine_tuned && pref.fine_tuned_model
      ? pref.fine_tuned_model
      : pref.model;

  return (
    <AdminView
      userName={user.full_name.split(" ")[0]}
      totalUsers={totalUsers}
      programsCount={programs.length}
      totalSubmissions={overview.total_submissions}
      plagiarismAlerts={overview.plagiarism_alerts}
      advisorFitAlerts={overview.advisor_fit_alerts}
      usersByRole={usersByRole}
      activeModel={activeModel}
      useFineTuned={!!pref.use_fine_tuned}
      ftEligible={ftStats.total_eligible}
      ftThreshold={ftStats.min_examples_threshold}
      providerAvailable={ftStats.provider_available}
    />
  );
}
