import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ProgramForm } from "@/features/programs/program-form";
import { ProgramRow } from "@/features/programs/program-row";
import { fetchPrograms } from "@/lib/api/programs";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Programas · KIMY" };

export default async function ProgramsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "admin") redirect(`/${user.role}`);

  const programs = await fetchPrograms();

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Administración
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Programas académicos</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Maestrías, doctorados y pregrados. Cada programa puede tener uno o
          varios documentos patrón asociados.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Crear programa</CardTitle>
          <CardDescription>
            Solo administradores. El código se almacena en mayúsculas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ProgramForm />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Programas registrados ({programs.length})</CardTitle>
          <CardDescription>
            Eliminar un programa borrará sus plantillas asociadas en cascada.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {programs.length === 0 ? (
            <p className="text-sm text-zinc-500">
              Aún no hay programas. Crea el primero arriba.
            </p>
          ) : (
            <ul className="space-y-2">
              {programs.map((p) => (
                <ProgramRow key={p.id} program={p} />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
