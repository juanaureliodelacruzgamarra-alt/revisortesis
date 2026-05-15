import { redirect } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LinkOrcidButton } from "@/features/orcid/link-button";
import { fetchOrcidPublications, fetchOrcidStatus } from "@/lib/api/orcid";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Mi perfil ORCID · KIMY" };

export default async function AdvisorProfilePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "advisor") redirect(`/${user.role}`);

  const status = await fetchOrcidStatus();
  const publications = status.linked ? await fetchOrcidPublications() : [];

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Asesor
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Mi perfil ORCID</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Vincula tu identidad académica con ORCID para que el sistema valide
          automáticamente la afinidad temática con cada avance que supervises.
        </p>
      </header>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Estado</CardTitle>
            <CardDescription>
              {status.linked
                ? "Tu cuenta ORCID está vinculada."
                : "Aún no has vinculado tu cuenta ORCID."}
            </CardDescription>
          </div>
          <LinkOrcidButton linked={status.linked} />
        </CardHeader>
        {status.linked ? (
          <CardContent>
            <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
              <dt className="text-zinc-500">ORCID iD</dt>
              <dd className="font-mono">
                {status.orcid_id ? (
                  <a
                    href={`https://orcid.org/${status.orcid_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline"
                  >
                    {status.orcid_id}
                  </a>
                ) : (
                  "—"
                )}
              </dd>
              <dt className="text-zinc-500">Afiliación</dt>
              <dd>{status.affiliation ?? "—"}</dd>
              <dt className="text-zinc-500">Última sincronización</dt>
              <dd>
                {status.last_sync
                  ? new Date(status.last_sync).toLocaleString("es-PE")
                  : "—"}
              </dd>
              <dt className="text-zinc-500">Publicaciones importadas</dt>
              <dd>{status.publications_count}</dd>
            </dl>
          </CardContent>
        ) : null}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Publicaciones ({publications.length})</CardTitle>
          <CardDescription>
            Los embeddings de estos títulos se usan para validar afinidad
            temática asesor↔tesis cuando el coordinador te asigna avances.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {publications.length === 0 ? (
            <p className="text-sm text-zinc-500">
              {status.linked
                ? "No se encontraron publicaciones públicas en tu ORCID."
                : "Vincula ORCID para ver tus publicaciones."}
            </p>
          ) : (
            <ul className="space-y-3">
              {publications.map((p) => (
                <li
                  key={p.id}
                  className="rounded-md border border-zinc-200 p-3 text-sm dark:border-zinc-800"
                >
                  <div className="flex flex-wrap items-baseline gap-2">
                    {p.year ? (
                      <Badge variant="muted">{p.year}</Badge>
                    ) : null}
                    {p.doi ? (
                      <a
                        href={`https://doi.org/${p.doi}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-mono text-xs text-zinc-500 hover:underline"
                      >
                        {p.doi}
                      </a>
                    ) : null}
                  </div>
                  <p className="mt-1 font-medium text-zinc-900 dark:text-zinc-100">
                    {p.title}
                  </p>
                  {p.journal ? (
                    <p className="text-xs italic text-zinc-500">{p.journal}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
