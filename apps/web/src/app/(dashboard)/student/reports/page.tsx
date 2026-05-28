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
import { SubmissionStatusBadge } from "@/features/submissions/status-badge";
import { fetchSubmissions } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";
import { SUBMISSION_STATUS_LABELS, type SubmissionStatus } from "@/lib/api/types";

export const metadata = { title: "Mis reportes · Aurelio" };

export default async function StudentReportsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "student") redirect(`/${user.role}`);

  const submissions = await fetchSubmissions();

  // Pre-compute counts by status for the KPI strip.
  const counts: Record<SubmissionStatus, number> = {
    draft: 0,
    in_progress: 0,
    observed: 0,
    approved: 0,
    rejected: 0,
  };
  for (const s of submissions) {
    counts[s.status as SubmissionStatus] += 1;
  }

  // Submissions that have at least one version are eligible to download the acta.
  const downloadable = submissions.filter(
    (s) => s.latest_version_number !== null,
  );

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Estudiante
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Mis reportes</h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Descarga el acta de revisión PDF de cada avance que ya pasó por el
          análisis de IA. Útil para adjuntarla a tus borradores o entregarla al
          jurado.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Avances" value={submissions.length} />
        <KpiCard label="En proceso" value={counts.in_progress} />
        <KpiCard
          label="Observados"
          value={counts.observed}
          tone={counts.observed > 0 ? "warning" : "default"}
        />
        <KpiCard
          label="Aprobados"
          value={counts.approved}
          tone={counts.approved > 0 ? "success" : "default"}
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Actas disponibles ({downloadable.length})</CardTitle>
          <CardDescription>
            El acta se genera al vuelo a partir de la última versión analizada.
            Incluye membrete Aurelio, resumen ejecutivo, hallazgos por
            severidad, plagio y validación de citas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {submissions.length === 0 ? (
            <div className="space-y-3 text-sm text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
              <p>Aún no tienes avances.</p>
              <Button asChild variant="outline" size="sm">
                <Link href="/student/submissions/new">Crear el primero</Link>
              </Button>
            </div>
          ) : (
            <ul className="space-y-2">
              {submissions.map((s) => {
                const ready = s.latest_version_number !== null;
                return (
                  <li
                    key={s.id}
                    className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)] sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <SubmissionStatusBadge status={s.status} />
                        <Badge variant="outline">[{s.program.code}]</Badge>
                        {s.latest_version_number ? (
                          <Badge variant="muted">
                            v{s.latest_version_number}
                          </Badge>
                        ) : null}
                      </div>
                      <p
                        className="mt-1 truncate font-medium"
                        title={s.title}
                      >
                        {s.title}
                      </p>
                      {s.chapter ? (
                        <p className="truncate text-xs text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
                          {s.chapter}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Button asChild variant="outline" size="sm">
                        <Link href={`/student/submissions/${s.id}`}>
                          Ver detalle
                        </Link>
                      </Button>
                      {ready ? (
                        <Button asChild size="sm">
                          <a
                            href={`/api/submissions/${s.id}/report.pdf`}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Descargar acta (PDF)
                          </a>
                        </Button>
                      ) : (
                        <Badge variant="muted" title="Sube una versión para generar el acta">
                          Sin versión
                        </Badge>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>¿Qué incluye el acta?</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1.5 text-sm">
            <li>• Membrete institucional Aurelio · UNT · Escuela de Posgrado.</li>
            <li>• Metadatos del avance (programa, capítulo, asesor, ORCID fit).</li>
            <li>• Resumen ejecutivo de IA + scores por dimensión + nota /20.</li>
            <li>• Hallazgos agrupados por severidad, con la acción del asesor.</li>
            <li>• Detección de plagio intra-programa y validación de citas (CrossRef).</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
