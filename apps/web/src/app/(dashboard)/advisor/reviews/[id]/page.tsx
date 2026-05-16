import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CitationsPanel } from "@/features/citations/citations-panel";
import { EvaluationPanel } from "@/features/evaluations/evaluation-panel";
import { FindingActions } from "@/features/evaluations/finding-actions";
import { PlagiarismPanel } from "@/features/plagiarism/matches-panel";
import {
  SubmissionStatusBadge,
  VersionStatusBadge,
} from "@/features/submissions/status-badge";
import { ApiError } from "@/lib/api/client";
import { fetchCitations } from "@/lib/api/citations";
import { fetchEvaluation } from "@/lib/api/evaluations";
import { fetchPlagiarismMatches } from "@/lib/api/plagiarism";
import { fetchSubmission } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Revisar avance · Aurelio" };

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default async function AdvisorReviewDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "advisor") redirect(`/${user.role}`);

  const { id } = await params;
  let submission;
  try {
    submission = await fetchSubmission(id);
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 403)) {
      notFound();
    }
    throw err;
  }

  const latestVersion = submission.versions[0];
  const [evaluation, plagiarismMatches, citations] = latestVersion
    ? await Promise.all([
        fetchEvaluation(submission.id, latestVersion.id),
        fetchPlagiarismMatches(submission.id, latestVersion.id),
        fetchCitations(submission.id, latestVersion.id),
      ])
    : [
        null,
        [] as Awaited<ReturnType<typeof fetchPlagiarismMatches>>,
        [] as Awaited<ReturnType<typeof fetchCitations>>,
      ];

  const downloadHref = latestVersion
    ? `/api/submissions/${submission.id}/versions/${latestVersion.id}/file`
    : null;

  const isPdf = latestVersion?.mime_type === "application/pdf";

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/advisor/reviews"
          className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-[color:var(--aurora-cream)]"
        >
          ← Volver a mis revisiones
        </Link>
      </div>

      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <SubmissionStatusBadge status={submission.status} />
          {latestVersion ? (
            <VersionStatusBadge status={latestVersion.parsing_status} />
          ) : null}
          <Badge variant="outline">[{submission.program.code}]</Badge>
          <span className="text-xs text-zinc-500">
            {submission.student.full_name} · {submission.student.email}
          </span>
        </div>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">
              {submission.title}
            </h1>
            {submission.chapter ? (
              <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
                {submission.chapter}
              </p>
            ) : null}
          </div>
          <Button asChild variant="outline">
            <a
              href={`/api/submissions/${submission.id}/report.pdf`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Descargar acta PDF
            </a>
          </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Documento</CardTitle>
              <CardDescription>
                {latestVersion ? (
                  <>
                    v{latestVersion.version_number} · {latestVersion.original_filename}
                    {" · "}
                    {formatSize(latestVersion.file_size_bytes)}
                  </>
                ) : (
                  "El estudiante aún no ha subido versiones."
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {latestVersion ? (
                <>
                  {isPdf && downloadHref ? (
                    <iframe
                      src={downloadHref}
                      className="h-[600px] w-full rounded-md border border-zinc-200 dark:border-[color:rgba(196,181,253,0.12)]"
                      title={latestVersion.original_filename}
                    />
                  ) : (
                    <p className="rounded-md border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-700 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(20,22,62,0.55)]/60 dark:text-[color:var(--aurora-cream-dim)]">
                      Vista previa no disponible para documentos Word. Descarga
                      el archivo para revisarlo.
                    </p>
                  )}
                  {downloadHref ? (
                    <Button asChild variant="outline" size="sm">
                      <a
                        href={downloadHref}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Descargar {latestVersion.original_filename}
                      </a>
                    </Button>
                  ) : null}
                </>
              ) : null}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <EvaluationPanel
            evaluation={evaluation}
            emptyMessage={
              latestVersion
                ? `Aún no hay evaluación. Estado: ${latestVersion.parsing_status}.`
                : "Sin versión subida — no hay nada que evaluar."
            }
            renderFindingExtra={(f) => (
              <FindingActions submissionId={submission.id} finding={f} />
            )}
          />
        </div>
      </div>

      <PlagiarismPanel
        matches={plagiarismMatches}
        emptyMessage="No se detectaron similitudes significativas (≥85%) con otros avances del programa."
      />

      <CitationsPanel
        citations={citations}
        emptyMessage="No se detectaron referencias bibliográficas en el avance (o la sección no se identificó). Asegúrate de incluir una sección 'Referencias' al final."
      />
    </div>
  );
}
