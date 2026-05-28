import { redirect } from "next/navigation";

import { AdvisorView } from "@/features/dashboard/advisor-view";
import { fetchSubmissions } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Asesor · Aurelio" };

export default async function AdvisorHome() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "advisor") redirect(`/${user.role}`);

  const reviews = await fetchSubmissions();

  const counts = reviews.reduce<Record<string, number>>((acc, s) => {
    acc[s.status] = (acc[s.status] ?? 0) + 1;
    return acc;
  }, {});
  const fitAlerts = reviews.filter((s) => s.advisor_fit_alert).length;
  const pending = (counts.in_progress ?? 0) + (counts.draft ?? 0);
  const approved = counts.approved ?? 0;

  const upcoming = reviews
    .filter((s) => s.status === "in_progress" || s.status === "observed")
    .slice(0, 4);

  return (
    <AdvisorView
      userName={user.full_name.split(" ")[0]}
      totalReviews={reviews.length}
      pending={pending}
      approved={approved}
      fitAlerts={fitAlerts}
      upcoming={upcoming}
    />
  );
}
