import { redirect } from "next/navigation";
import { cookies } from "next/headers";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { finishOrcidLinkAction } from "@/lib/api/orcid";
import { getSession } from "@/lib/auth/session";

const STATE_COOKIE = "kimy.orcid.state";

export const metadata = { title: "Vinculando ORCID… · Aurelio" };

export default async function OrcidCallbackPage({
  searchParams,
}: {
  searchParams: Promise<{ code?: string; state?: string; error?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (session.role !== "advisor") redirect(`/${session.role}`);

  const params = await searchParams;
  const code = params.code ?? "";
  const state = params.state ?? "";
  const error = params.error ?? "";

  const jar = await cookies();
  const expectedState = jar.get(STATE_COOKIE)?.value ?? "";
  // The state cookie has a 10-min max-age so it auto-expires. Next.js 16 forbids
  // mutating cookies from a Server Component, so we don't actively delete it.

  let outcome: { ok: true; orcidId: string | null; publications: number; mode: string } | { ok: false; error: string };
  if (error) {
    outcome = { ok: false, error: `ORCID devolvió un error: ${error}` };
  } else if (!code || !state) {
    outcome = { ok: false, error: "Faltan parámetros code/state en el callback." };
  } else if (!expectedState) {
    outcome = {
      ok: false,
      error: "No se encontró el state esperado en cookies. Inicia la vinculación de nuevo desde tu perfil.",
    };
  } else {
    const result = await finishOrcidLinkAction(code, state, expectedState);
    if (result.ok) {
      outcome = {
        ok: true,
        orcidId: result.result.orcid_id,
        publications: result.result.publications_count,
        mode: result.result.backend,
      };
    } else {
      outcome = { ok: false, error: result.error };
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-16 dark:bg-black">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>
            {outcome.ok ? "ORCID vinculado" : "No pudimos vincular ORCID"}
          </CardTitle>
          <CardDescription>
            {outcome.ok
              ? "Tus publicaciones se han sincronizado y están listas para la validación de afinidad temática."
              : outcome.error}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {outcome.ok ? (
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <dt className="text-zinc-500">ORCID iD</dt>
              <dd className="font-mono">{outcome.orcidId ?? "—"}</dd>
              <dt className="text-zinc-500">Publicaciones</dt>
              <dd>{outcome.publications}</dd>
              <dt className="text-zinc-500">Backend</dt>
              <dd className="font-mono">{outcome.mode}</dd>
            </dl>
          ) : null}
          <a
            href="/advisor/profile"
            className="text-sm font-medium underline-offset-4 hover:underline"
          >
            ← Volver a mi perfil
          </a>
        </CardContent>
      </Card>
    </main>
  );
}
