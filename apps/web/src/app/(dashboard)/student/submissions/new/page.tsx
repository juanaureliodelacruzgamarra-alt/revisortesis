import Link from "next/link";
import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SubmissionForm } from "@/features/submissions/submission-form";
import { fetchPrograms } from "@/lib/api/programs";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Nuevo avance · KIMY" };

export default async function NewSubmissionPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "student") redirect(`/${user.role}`);

  const programs = await fetchPrograms();

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/student/submissions"
          className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          ← Volver a mis avances
        </Link>
      </div>

      <header className="space-y-1">
        <h1 className="text-3xl font-semibold tracking-tight">Nuevo avance</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Primero crea la entrada del avance. En el detalle podrás subir las
          versiones (.docx o .pdf).
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Datos del avance</CardTitle>
          <CardDescription>
            Si tu programa tiene un documento patrón activo, se asociará
            automáticamente.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SubmissionForm programs={programs} />
        </CardContent>
      </Card>
    </div>
  );
}
