import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FiltersBar } from "@/features/submissions/filters-bar";
import { SelectableSubmissionsList } from "@/features/submissions/selectable-list";
import { fetchPrograms } from "@/lib/api/programs";
import {
  fetchEligibleAdvisors,
  fetchSubmissions,
  type SubmissionFilters,
} from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Avances del programa · Aurelio" };

export default async function CoordinatorSubmissionsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "coordinator" && user.role !== "admin") {
    redirect(`/${user.role}`);
  }

  const sp = await searchParams;
  const filters: SubmissionFilters = {
    program_id: typeof sp.program_id === "string" ? sp.program_id : undefined,
    status: typeof sp.status === "string" ? sp.status : undefined,
    fit_alert: sp.fit_alert === "true" ? true : undefined,
  };

  const [submissions, programs, advisors] = await Promise.all([
    fetchSubmissions(filters),
    fetchPrograms(),
    fetchEligibleAdvisors(),
  ]);

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Coordinador
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Avances</h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Filtra por programa, estado y alerta ORCID. Asigna o cambia el asesor
          de cada avance — la afinidad temática se recalcula automáticamente.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>
            Los cambios se aplican en vivo. Los filtros van en la URL.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FiltersBar programs={programs} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resultados ({submissions.length})</CardTitle>
          <CardDescription>
            Selecciona varios avances para aplicar acciones en lote o descargar
            un reporte comparativo en CSV.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {submissions.length === 0 ? (
            <p className="text-sm text-zinc-500">
              No hay avances que coincidan con los filtros.
            </p>
          ) : (
            <SelectableSubmissionsList
              submissions={submissions}
              advisors={advisors}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
