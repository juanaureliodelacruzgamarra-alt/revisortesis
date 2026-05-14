import Link from "next/link";
import { redirect } from "next/navigation";

import { Button } from "@/components/ui/button";
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

export const metadata = { title: "Mis avances · KIMY" };

export default async function StudentSubmissionsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "student") redirect(`/${user.role}`);

  const submissions = await fetchSubmissions();

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
            Estudiante
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">Mis avances</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Crea un avance y sube las versiones (.docx o .pdf) que quieras
            revisar.
          </p>
        </div>
        <Button asChild>
          <Link href="/student/submissions/new">Nuevo avance</Link>
        </Button>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Avances ({submissions.length})</CardTitle>
          <CardDescription>
            Cada avance puede tener múltiples versiones. La última versión es la
            que será revisada por la IA y tu asesor.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {submissions.length === 0 ? (
            <div className="space-y-3 text-sm text-zinc-500">
              <p>Aún no tienes avances.</p>
              <Button asChild variant="outline" size="sm">
                <Link href="/student/submissions/new">Crear el primero</Link>
              </Button>
            </div>
          ) : (
            <ul className="space-y-2">
              {submissions.map((s) => (
                <SubmissionRow
                  key={s.id}
                  submission={s}
                  basePath="/student/submissions"
                />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
