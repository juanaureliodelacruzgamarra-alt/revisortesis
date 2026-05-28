import { redirect } from "next/navigation";

import { StudentView } from "@/features/dashboard/student-view";
import { fetchSubmissions } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Estudiante · Aurelio" };

export default async function StudentHome() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "student") redirect(`/${user.role}`);

  const submissions = await fetchSubmissions();

  const counts = submissions.reduce<Record<string, number>>((acc, s) => {
    acc[s.status] = (acc[s.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <StudentView
      userName={user.full_name.split(" ")[0]}
      submissions={submissions}
      inProgress={counts.in_progress ?? 0}
      observed={counts.observed ?? 0}
      approved={counts.approved ?? 0}
      recent={submissions.slice(0, 3)}
    />
  );
}
