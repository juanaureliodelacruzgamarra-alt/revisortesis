import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { KpiCard } from "@/features/dashboard/kpi-card";
import { SubmissionRow } from "@/features/submissions/submission-row";
import { fetchSubmissions } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";
import { ROLE_LABELS } from "@/lib/auth/types";

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
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          {ROLE_LABELS.advisor}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Hola, {user.full_name.split(" ")[0]}
        </h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Aquí tienes el resumen de los avances que te corresponden revisar.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Asignados" value={reviews.length} />
        <KpiCard label="Pendientes" value={pending} tone={pending > 0 ? "warning" : "default"} />
        <KpiCard label="Aprobados" value={approved} tone={approved > 0 ? "success" : "default"} />
        <KpiCard
          label="Alerta ORCID fit"
          value={fitAlerts}
          tone={fitAlerts > 0 ? "warning" : "default"}
          helper="afinidad temática baja"
        />
      </section>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <div>
            <CardTitle>Por revisar</CardTitle>
            <CardDescription>Avances activos asignados a ti.</CardDescription>
          </div>
          <Badge variant="muted">{upcoming.length}</Badge>
        </CardHeader>
        <CardContent>
          {upcoming.length === 0 ? (
            <p className="text-sm text-zinc-500">
              No hay avances pendientes. Cuando un estudiante suba una nueva versión, aparecerá aquí.
            </p>
          ) : (
            <ul className="space-y-2">
              {upcoming.map((s) => (
                <SubmissionRow
                  key={s.id}
                  submission={s}
                  basePath="/advisor/reviews"
                  showStudent
                />
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-zinc-500">
            <Link href="/advisor/reviews" className="underline">
              Ver todas las revisiones →
            </Link>{" "}
            ·{" "}
            <Link href="/advisor/profile" className="underline">
              Mi perfil ORCID →
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
