import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SubmissionRow } from "@/features/submissions/submission-row";
import { fetchSubmissions } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Revisiones · Aurelio" };

export default async function AdvisorReviewsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "advisor") redirect(`/${user.role}`);

  const submissions = await fetchSubmissions();

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Asesor
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Mis revisiones</h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Avances asignados a tu cuenta. La pantalla de revisión lado-a-lado y
          la validación de hallazgos IA llegarán en la Fase 4.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Asignados ({submissions.length})</CardTitle>
          <CardDescription>
            La asignación de asesores se hace desde el panel de coordinador.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {submissions.length === 0 ? (
            <p className="text-sm text-zinc-500">
              No tienes avances asignados aún. Pide al coordinador que te asigne
              tesistas desde el panel de gestión.
            </p>
          ) : (
            <ul className="space-y-2">
              {submissions.map((s) => (
                <SubmissionRow
                  key={s.id}
                  submission={s}
                  basePath="/advisor/reviews"
                  showStudent
                />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
