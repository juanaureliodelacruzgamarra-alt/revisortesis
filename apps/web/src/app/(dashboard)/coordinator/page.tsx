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
import { ProgramBars } from "@/features/dashboard/program-bars";
import { StatusDonut } from "@/features/dashboard/status-donut";
import { fetchStatsActivity, fetchStatsOverview } from "@/lib/api/stats";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Dashboard · KIMY" };

function formatPct(v: number | null) {
  return v === null ? "—" : `${v.toFixed(1)}%`;
}
function formatGrade(v: number | null) {
  return v === null ? "—" : v.toFixed(2);
}

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
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Coordinador
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          KPIs agregados de todos los programas. La Fase 9 añadirá revisión por
          lotes y exportación de reportes consolidados.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard label="Avances totales" value={stats.total_submissions} />
        <KpiCard
          label="Nota IA promedio"
          value={formatGrade(stats.avg_ai_grade)}
          helper={`/ 20 · ${formatPct(stats.avg_ai_percentage)} de cumplimiento`}
        />
        <KpiCard
          label="Concordancia IA-Humano"
          value={formatPct(stats.ai_human_concordance_pct)}
          helper="% de hallazgos aceptados sin modificar"
        />
        <KpiCard
          label="Asesores con ORCID"
          value={stats.total_advisors_with_orcid}
        />
        <KpiCard
          label="Alertas de plagio"
          value={stats.plagiarism_alerts}
          tone={stats.plagiarism_alerts > 0 ? "danger" : "default"}
          helper="similitud ≥ 85% intra-programa"
        />
        <KpiCard
          label="Alertas ORCID fit"
          value={stats.advisor_fit_alerts}
          tone={stats.advisor_fit_alerts > 0 ? "warning" : "default"}
          helper="asesor↔tesis poco afín"
        />
        <KpiCard
          label="Bajo cumplimiento"
          value={stats.low_compliance_submissions}
          tone={stats.low_compliance_submissions > 0 ? "warning" : "default"}
          helper="< 60% en evaluación IA"
        />
        <KpiCard
          label="Citas problemáticas"
          value={stats.citations_problematic}
          helper={`de ${stats.citations_total} extraídas`}
          tone={stats.citations_problematic > 0 ? "warning" : "default"}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Distribución por estado</CardTitle>
            <CardDescription>
              Cantidad de avances en cada etapa del flujo.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StatusDonut data={stats.submissions_by_status} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Nota IA promedio por programa</CardTitle>
            <CardDescription>
              Promedio de la última evaluación IA por avance, sobre 20.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ProgramBars data={stats.grades_per_program} />
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Actividad reciente</CardTitle>
          <CardDescription>
            Últimos {activity.length} eventos relevantes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {activity.length === 0 ? (
            <p className="text-sm text-zinc-500">Sin actividad reciente.</p>
          ) : (
            <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {activity.map((a, idx) => (
                <li
                  key={`${a.submission_id}-${a.occurred_at}-${idx}`}
                  className="flex items-start justify-between gap-3 py-3 text-sm"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-zinc-900 dark:text-zinc-50">
                      {a.description}
                    </p>
                    <p className="truncate text-xs text-zinc-500">
                      {a.submission_title} · {a.actor_name}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge variant="outline" className="font-mono text-xs">
                      {a.kind.replace(/_/g, " ")}
                    </Badge>
                    <span className="text-xs text-zinc-500">
                      {new Date(a.occurred_at).toLocaleString("es-PE")}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
