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
import { fetchFineTuningStats, fetchModelPreference } from "@/lib/api/fine-tuning";
import { fetchPrograms } from "@/lib/api/programs";
import { fetchStatsOverview } from "@/lib/api/stats";
import { fetchAdminUsers } from "@/lib/api/users";
import { getCurrentUser } from "@/lib/auth/session";
import { ROLE_LABELS } from "@/lib/auth/types";

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
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          {ROLE_LABELS.admin}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Hola, {user.full_name.split(" ")[0]}
        </h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Panorama del sistema en este momento.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Usuarios" value={totalUsers} helper={`${programs.length} programas`} />
        <KpiCard label="Avances totales" value={overview.total_submissions} />
        <KpiCard
          label="Alertas plagio"
          value={overview.plagiarism_alerts}
          tone={overview.plagiarism_alerts > 0 ? "warning" : "default"}
        />
        <KpiCard
          label="Alertas ORCID"
          value={overview.advisor_fit_alerts}
          tone={overview.advisor_fit_alerts > 0 ? "warning" : "default"}
        />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Distribución por rol</CardTitle>
            <CardDescription>Cuentas activas e inactivas combinadas.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {(["student", "advisor", "coordinator", "admin"] as const).map(
                (r) => (
                  <li key={r} className="flex items-center justify-between">
                    <span>{ROLE_LABELS[r]}</span>
                    <Badge variant="muted">{usersByRole[r] ?? 0}</Badge>
                  </li>
                ),
              )}
            </ul>
            <p className="mt-3 text-xs text-zinc-500">
              <Link href="/admin/users" className="underline">
                Gestionar usuarios →
              </Link>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>IA y fine-tuning</CardTitle>
            <CardDescription>
              Modelo en producción y avance del entrenamiento personalizado.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span>Modelo activo</span>
              <Badge variant={pref.use_fine_tuned ? "success" : "muted"}>
                {activeModel}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Feedback elegible</span>
              <Badge variant="muted">
                {ftStats.total_eligible} / {ftStats.min_examples_threshold}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Tuning programático</span>
              <Badge
                variant={ftStats.provider_available ? "success" : "warning"}
              >
                {ftStats.provider_available ? "sí" : "no"}
              </Badge>
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              <Link href="/admin/settings" className="underline">
                Ajustar configuración →
              </Link>{" "}
              ·{" "}
              <Link href="/admin/fine-tuning" className="underline">
                Ver pipeline →
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Accesos rápidos</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
            <li>
              <Link href="/admin/users" className="underline">
                Crear o desactivar usuarios
              </Link>
            </li>
            <li>
              <Link href="/admin/programs" className="underline">
                Administrar programas académicos
              </Link>
            </li>
            <li>
              <Link href="/admin/settings" className="underline">
                Configuración del sistema
              </Link>
            </li>
            <li>
              <Link href="/admin/fine-tuning" className="underline">
                Pipeline de fine-tuning
              </Link>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
