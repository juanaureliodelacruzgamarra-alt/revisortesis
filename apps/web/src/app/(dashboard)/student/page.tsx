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
import { SubmissionRow } from "@/features/submissions/submission-row";
import { fetchSubmissions } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";
import { ROLE_LABELS } from "@/lib/auth/types";

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

  const inProgress = counts.in_progress ?? 0;
  const observed = counts.observed ?? 0;
  const approved = counts.approved ?? 0;

  const recent = submissions.slice(0, 3);

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          {ROLE_LABELS.student}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Hola, {user.full_name.split(" ")[0]}
        </h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Sube tus avances, revisa los hallazgos de la IA y atiende las
          observaciones del asesor.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Avances totales" value={submissions.length} />
        <KpiCard label="En proceso" value={inProgress} />
        <KpiCard
          label="Observados"
          value={observed}
          tone={observed > 0 ? "warning" : "default"}
        />
        <KpiCard label="Aprobados" value={approved} tone={approved > 0 ? "success" : "default"} />
      </section>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <div>
            <CardTitle>Últimos avances</CardTitle>
            <CardDescription>
              Tus 3 entregas más recientes. El detalle muestra hallazgos IA y citaciones.
            </CardDescription>
          </div>
          <Button asChild size="sm">
            <Link href="/student/submissions/new">Nuevo avance</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {recent.length === 0 ? (
            <p className="text-sm text-zinc-500">
              Aún no tienes avances. Crea el primero con el botón de arriba.
            </p>
          ) : (
            <ul className="space-y-2">
              {recent.map((s) => (
                <SubmissionRow
                  key={s.id}
                  submission={s}
                  basePath="/student/submissions"
                />
              ))}
            </ul>
          )}
          {submissions.length > recent.length ? (
            <p className="mt-3 text-xs text-zinc-500">
              <Link href="/student/submissions" className="underline">
                Ver todos los avances ({submissions.length}) →
              </Link>
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>¿Cómo funciona?</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-2 text-sm">
            <li>
              <Badge variant="muted">1</Badge> Crea un avance indicando programa, título y capítulo.
            </li>
            <li>
              <Badge variant="muted">2</Badge> Sube el archivo Word/PDF de tu avance.
            </li>
            <li>
              <Badge variant="muted">3</Badge> Aurelio analiza estructura, contenido, citas y plagio.
            </li>
            <li>
              <Badge variant="muted">4</Badge> Tu asesor valida los hallazgos. Recibes una notificación cuando hay cambios.
            </li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
