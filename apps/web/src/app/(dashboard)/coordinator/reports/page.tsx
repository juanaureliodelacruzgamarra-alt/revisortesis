import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { KpiCard } from "@/features/dashboard/kpi-card";
import { fetchPrograms } from "@/lib/api/programs";
import {
  fetchProgramsRollup,
  fetchSubmissionsReport,
} from "@/lib/api/reports";
import { fetchStatsOverview } from "@/lib/api/stats";
import { getCurrentUser } from "@/lib/auth/session";
import { SUBMISSION_STATUS_LABELS, type SubmissionStatus } from "@/lib/api/types";

export const metadata = { title: "Reportes · Aurelio" };

const STATUSES: SubmissionStatus[] = [
  "draft",
  "in_progress",
  "observed",
  "approved",
  "rejected",
];

function formatGrade(v: number | null) {
  return v === null ? "—" : v.toFixed(2);
}
function formatPct(v: number | null) {
  return v === null ? "—" : `${v.toFixed(1)}%`;
}

type SearchParams = Promise<{
  program_id?: string;
  status?: string;
}>;

export default async function CoordinatorReportsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "coordinator" && user.role !== "admin") {
    redirect(`/${user.role}`);
  }

  const params = await searchParams;
  const programFilter = params.program_id ?? "";
  const statusFilter = params.status ?? "";

  const [overview, rollup, report, programs] = await Promise.all([
    fetchStatsOverview(),
    fetchProgramsRollup(),
    fetchSubmissionsReport({
      program_id: programFilter || undefined,
      status: statusFilter || undefined,
    }),
    fetchPrograms(),
  ]);

  // Build the export query string mirroring the current filters.
  const exportQs = new URLSearchParams();
  if (programFilter) exportQs.set("program_id", programFilter);
  if (statusFilter) exportQs.set("status", statusFilter);
  const exportSuffix = exportQs.toString() ? `?${exportQs.toString()}` : "";
  const submissionsCsvHref = `/api/reports/submissions.csv${exportSuffix}`;
  const submissionsPdfHref = `/api/reports/submissions.pdf${exportSuffix}`;

  // Subset of submissions with alerts — useful "needs attention" table.
  const flagged = report.rows.filter(
    (r) =>
      r.advisor_fit_alert ||
      (r.total_percentage !== null && r.total_percentage < 60),
  );

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-2xl space-y-1">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
            Coordinador
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">Reportes</h1>
          <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
            Vista consolidada de avances, métricas por programa y exportaciones
            listas para auditoría o reuniones con la escuela.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild>
            <a
              href="/api/reports/executive.pdf"
              target="_blank"
              rel="noopener noreferrer"
            >
              Reporte ejecutivo (PDF)
            </a>
          </Button>
          <Button asChild variant="outline">
            <a
              href="/api/reports/activity.pdf"
              target="_blank"
              rel="noopener noreferrer"
            >
              Actividad (PDF)
            </a>
          </Button>
        </div>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Avances" value={overview.total_submissions} />
        <KpiCard
          label="Nota IA promedio"
          value={formatGrade(overview.avg_ai_grade)}
          helper={`/ 20 · ${formatPct(overview.avg_ai_percentage)}`}
        />
        <KpiCard
          label="Bajo cumplimiento"
          value={overview.low_compliance_submissions}
          tone={overview.low_compliance_submissions > 0 ? "warning" : "default"}
          helper="< 60% en IA"
        />
        <KpiCard
          label="Alertas críticas"
          value={overview.plagiarism_alerts + overview.advisor_fit_alerts}
          tone={
            overview.plagiarism_alerts + overview.advisor_fit_alerts > 0
              ? "danger"
              : "default"
          }
          helper="plagio + ORCID fit"
        />
      </section>

      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <CardTitle>Rollup por programa</CardTitle>
            <CardDescription>
              Métricas agregadas por programa. Incluye avances totales, nota IA
              promedio y alertas activas.
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline" size="sm">
              <a href="/api/reports/programs.csv">CSV</a>
            </Button>
            <Button asChild size="sm">
              <a
                href="/api/reports/programs.pdf"
                target="_blank"
                rel="noopener noreferrer"
              >
                PDF
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {rollup.rows.length === 0 ? (
            <p className="text-sm text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
              Aún no hay programas con avances registrados.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-200 text-left text-xs font-medium uppercase tracking-widest text-zinc-500 dark:border-[color:rgba(196,181,253,0.12)] dark:text-[color:var(--aurora-cream-dim)]">
                    <th className="py-2 pr-4">Código</th>
                    <th className="py-2 pr-4">Programa</th>
                    <th className="py-2 pr-4 text-right">Avances</th>
                    <th className="py-2 pr-4 text-right">Nota IA</th>
                    <th className="py-2 pr-4 text-right">Plagio</th>
                    <th className="py-2 text-right">ORCID fit</th>
                  </tr>
                </thead>
                <tbody>
                  {rollup.rows.map((r) => (
                    <tr
                      key={r.program_id}
                      className="border-b border-zinc-100 last:border-0 dark:border-[color:rgba(196,181,253,0.08)]"
                    >
                      <td className="py-2 pr-4">
                        <Badge variant="outline">{r.program_code}</Badge>
                      </td>
                      <td className="py-2 pr-4">{r.program_name}</td>
                      <td className="py-2 pr-4 text-right tabular-nums">
                        {r.submissions_count}
                      </td>
                      <td className="py-2 pr-4 text-right tabular-nums">
                        {formatGrade(r.average_grade)}
                      </td>
                      <td className="py-2 pr-4 text-right tabular-nums">
                        {r.plagiarism_alerts > 0 ? (
                          <Badge variant="destructive">
                            {r.plagiarism_alerts}
                          </Badge>
                        ) : (
                          <span className="text-zinc-400">0</span>
                        )}
                      </td>
                      <td className="py-2 text-right tabular-nums">
                        {r.fit_alerts > 0 ? (
                          <Badge variant="warning">{r.fit_alerts}</Badge>
                        ) : (
                          <span className="text-zinc-400">0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <CardTitle>Listado de avances ({report.total})</CardTitle>
            <CardDescription>
              Aplica filtros y descarga el reporte con la selección actual.
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline" size="sm">
              <a href={submissionsCsvHref}>CSV</a>
            </Button>
            <Button asChild size="sm">
              <a
                href={submissionsPdfHref}
                target="_blank"
                rel="noopener noreferrer"
              >
                PDF
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <form method="GET" className="flex flex-wrap gap-2 text-sm">
            <select
              name="program_id"
              defaultValue={programFilter}
              className="h-9 rounded-md border border-zinc-200 bg-white px-2 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)]"
            >
              <option value="">Todos los programas</option>
              {programs.map((p) => (
                <option key={p.id} value={p.id}>
                  [{p.code}] {p.name}
                </option>
              ))}
            </select>
            <select
              name="status"
              defaultValue={statusFilter}
              className="h-9 rounded-md border border-zinc-200 bg-white px-2 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)]"
            >
              <option value="">Todos los estados</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {SUBMISSION_STATUS_LABELS[s]}
                </option>
              ))}
            </select>
            <Button type="submit" size="sm">
              Filtrar
            </Button>
            {programFilter || statusFilter ? (
              <Button asChild variant="ghost" size="sm">
                <Link href="/coordinator/reports">Limpiar</Link>
              </Button>
            ) : null}
          </form>

          {report.rows.length === 0 ? (
            <p className="text-sm text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
              No hay avances que coincidan con los filtros.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-200 text-left text-xs font-medium uppercase tracking-widest text-zinc-500 dark:border-[color:rgba(196,181,253,0.12)] dark:text-[color:var(--aurora-cream-dim)]">
                    <th className="py-2 pr-3">Programa</th>
                    <th className="py-2 pr-3">Título</th>
                    <th className="py-2 pr-3">Estudiante</th>
                    <th className="py-2 pr-3">Asesor</th>
                    <th className="py-2 pr-3">Estado</th>
                    <th className="py-2 pr-3 text-right">Nota IA</th>
                    <th className="py-2 text-right">Alertas</th>
                  </tr>
                </thead>
                <tbody>
                  {report.rows.map((r) => (
                    <tr
                      key={r.submission_id}
                      className="border-b border-zinc-100 last:border-0 dark:border-[color:rgba(196,181,253,0.08)]"
                    >
                      <td className="py-2 pr-3">
                        <Badge variant="outline">{r.program_code}</Badge>
                      </td>
                      <td className="py-2 pr-3">
                        <p className="font-medium" title={r.title}>
                          {r.title}
                        </p>
                        {r.chapter ? (
                          <p className="text-xs text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
                            {r.chapter}
                          </p>
                        ) : null}
                      </td>
                      <td className="py-2 pr-3 text-xs">{r.student_name}</td>
                      <td className="py-2 pr-3 text-xs">
                        {r.advisor_name ?? "—"}
                      </td>
                      <td className="py-2 pr-3">
                        <Badge variant="muted">
                          {SUBMISSION_STATUS_LABELS[r.status as SubmissionStatus] ??
                            r.status}
                        </Badge>
                      </td>
                      <td className="py-2 pr-3 text-right tabular-nums">
                        {r.decimal_grade !== null
                          ? r.decimal_grade.toFixed(2)
                          : "—"}
                      </td>
                      <td className="py-2 text-right">
                        <div className="flex flex-wrap justify-end gap-1">
                          {r.advisor_fit_alert ? (
                            <Badge variant="warning">ORCID</Badge>
                          ) : null}
                          {r.total_percentage !== null &&
                          r.total_percentage < 60 ? (
                            <Badge variant="destructive">bajo</Badge>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {flagged.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Necesitan atención ({flagged.length})</CardTitle>
            <CardDescription>
              Avances con afinidad ORCID baja o cumplimiento IA &lt; 60%.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {flagged.map((r) => (
                <li
                  key={r.submission_id}
                  className="flex flex-col gap-1 rounded-md border border-zinc-200 p-3 dark:border-[color:rgba(196,181,253,0.12)] sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium">{r.title}</p>
                    <p className="truncate text-xs text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
                      {r.student_name} · {r.program_code}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {r.advisor_fit_alert ? (
                      <Badge variant="warning">ORCID fit</Badge>
                    ) : null}
                    {r.total_percentage !== null &&
                    r.total_percentage < 60 ? (
                      <Badge variant="destructive">
                        IA {r.total_percentage.toFixed(0)}%
                      </Badge>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
