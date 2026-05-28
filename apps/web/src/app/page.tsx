import Link from "next/link";
import { redirect } from "next/navigation";

import { Button } from "@/components/ui/button";
import { getSession } from "@/lib/auth/session";
import { ROLE_HOMES } from "@/lib/auth/types";
import { API_URL } from "@/lib/env";

type Health = { status: string; service: string; version: string };

async function fetchHealth(): Promise<Health | null> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as Health;
  } catch {
    return null;
  }
}

export default async function Home() {
  const session = await getSession();
  if (session) redirect(ROLE_HOMES[session.role]);

  const health = await fetchHealth();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 px-6 py-16 dark:bg-black">
      <div className="w-full max-w-2xl space-y-8">
        <header className="space-y-2 text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-zinc-500">
            Plataforma Aurelio
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 dark:text-[color:var(--aurora-cream)]">
            Revisión inteligente de tesis
          </h1>
          <p className="mx-auto max-w-xl text-base text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
            Gestión, evaluación con IA, detección de plagio y validación
            bibliográfica para avances académicos.
          </p>
        </header>

        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Button asChild className="w-full sm:w-auto">
            <Link href="/login">Iniciar sesión</Link>
          </Button>
          <Button asChild variant="outline" className="w-full sm:w-auto">
            <Link href="/register">Crear cuenta</Link>
          </Button>
        </div>

        <div className="flex justify-center">
          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
              health
                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                : "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                health ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            API {health ? `${health.service} v${health.version}` : "offline"}
          </span>
        </div>
      </div>
    </main>
  );
}
