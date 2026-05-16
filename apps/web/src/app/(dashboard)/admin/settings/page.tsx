import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ModelToggle } from "@/features/fine-tuning/model-toggle";
import { FtThresholdForm } from "@/features/settings/ft-threshold-form";
import { fetchModelPreference } from "@/lib/api/fine-tuning";
import { fetchSystemSettings } from "@/lib/api/settings";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Configuración · Aurelio" };

export default async function SettingsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "admin") redirect(`/${user.role}`);

  const [settings, pref] = await Promise.all([
    fetchSystemSettings(),
    fetchModelPreference(),
  ]);
  const ftRow = settings.find((s) => s.key === "ai.fine_tuning");
  const minExamples = Number(ftRow?.value.min_examples ?? 500);

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Administración
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Configuración</h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          Ajustes operativos del sistema. Los cambios se aplican en caliente sin reinicio.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Modelo IA activo</CardTitle>
          <CardDescription>
            Selecciona el modelo base de OpenAI y, si tienes un fine-tuneado disponible, activa el toggle A/B.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ModelToggle pref={pref} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fine-tuning</CardTitle>
          <CardDescription>
            Configura cuántos ejemplos de feedback humano son necesarios antes
            de permitir subir el dataset a OpenAI.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FtThresholdForm minExamples={minExamples} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Estado actual</CardTitle>
          <CardDescription>
            Valores aplicados ahora mismo. Útil para auditar cambios.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            {settings.map((s) => (
              <div key={s.key} className="space-y-1">
                <dt className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                  {s.key}
                </dt>
                <dd>
                  <pre className="overflow-x-auto rounded-md bg-zinc-50 p-2 text-xs dark:bg-[rgba(20,22,62,0.55)]">
                    {JSON.stringify(s.value, null, 2)}
                  </pre>
                  {s.updated_at ? (
                    <p className="mt-1 text-xs text-zinc-500">
                      última actualización: {new Date(s.updated_at).toLocaleString("es-PE")}
                    </p>
                  ) : (
                    <p className="mt-1 text-xs text-zinc-400">valor por defecto (sin override)</p>
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
