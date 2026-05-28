import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { TemplateCard } from "@/features/templates/template-card";
import { TemplateForm } from "@/features/templates/template-form";
import { fetchPrograms } from "@/lib/api/programs";
import { fetchTemplates } from "@/lib/api/templates";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Documentos patrón · Aurelio" };

export default async function CoordinatorTemplatesPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "coordinator" && user.role !== "admin") {
    redirect(`/${user.role}`);
  }

  const [programs, templates] = await Promise.all([
    fetchPrograms(),
    fetchTemplates(),
  ]);

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Coordinador
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Documentos patrón
        </h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Sube la plantilla institucional (Word o PDF) para cada programa. El
          sistema extrae automáticamente la estructura de secciones.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Subir nueva plantilla</CardTitle>
          <CardDescription>
            La versión se incrementa automáticamente por programa.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TemplateForm programs={programs} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Plantillas registradas ({templates.length})</CardTitle>
          <CardDescription>
            Activa la versión vigente para cada programa.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {templates.length === 0 ? (
            <p className="text-sm text-zinc-500">
              Aún no hay plantillas. Sube la primera arriba.
            </p>
          ) : (
            <ul className="space-y-2">
              {templates.map((t) => (
                <TemplateCard key={t.id} template={t} />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
