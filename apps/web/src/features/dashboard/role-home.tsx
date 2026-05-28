import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ROLE_LABELS, type UserRole } from "@/lib/auth/types";
import { getCurrentUser } from "@/lib/auth/session";

type Props = {
  expectedRole: UserRole;
  description: string;
  upcoming: string[];
};

export async function RoleHome({ expectedRole, description, upcoming }: Props) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== expectedRole) {
    redirect(`/${user.role}`);
  }

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          {ROLE_LABELS[user.role]}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Hola, {user.full_name.split(" ")[0]}
        </h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">{description}</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Tu sesión</CardTitle>
          <CardDescription>
            Información obtenida desde el backend Aurelio.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <dt className="text-zinc-500">ID</dt>
            <dd className="font-mono">{user.id}</dd>
            <dt className="text-zinc-500">Correo</dt>
            <dd>{user.email}</dd>
            <dt className="text-zinc-500">Rol</dt>
            <dd>{ROLE_LABELS[user.role]}</dd>
            <dt className="text-zinc-500">Creado</dt>
            <dd>{new Date(user.created_at).toLocaleString("es-PE")}</dd>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Próximas funcionalidades</CardTitle>
          <CardDescription>
            Lo que llegará a este panel en las siguientes fases.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-zinc-700 dark:text-[color:var(--aurora-cream-dim)]">
            {upcoming.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
