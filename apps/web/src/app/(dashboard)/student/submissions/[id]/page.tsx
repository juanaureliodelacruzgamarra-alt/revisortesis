import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CitationsPanel } from "@/features/citations/citations-panel";
import { EvaluationPanel } from "@/features/evaluations/evaluation-panel";
import { SubmissionStatusBadge } from "@/features/submissions/status-badge";
import { VersionList } from "@/features/submissions/version-list";
import { VersionUploader } from "@/features/submissions/version-uploader";
import { ApiError } from "@/lib/api/client";
import { fetchCitations } from "@/lib/api/citations";
import { fetchEvaluation } from "@/lib/api/evaluations";
import { fetchSubmission } from "@/lib/api/submissions";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Avance · KIMY" };

export default async function StudentSubmissionDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "student") redirect(`/${user.role}`);

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

  const latestVersion = submission.versions[0]; // versions arrive sorted desc
  const [evaluation, citations] = latestVersion
    ? await Promise.all([
        fetchEvaluation(submission.id, latestVersion.id),
        fetchCitations(submission.id, latestVersion.id),
      ])
    : [null, [] as Awaited<ReturnType<typeof fetchCitations>>];

  const evaluationEmptyMessage = !latestVersion
    ? "Sube una versión para activar el análisis."
    : latestVersion.parsing_status === "ai_completed"
      ? "Evaluación cargando…"
      : `Aún no hay evaluación. Estado actual: ${latestVersion.parsing_status}.`;

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/student/submissions"
          className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          ← Volver a mis avances
        </Link>
      </div>

      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <SubmissionStatusBadge status={submission.status} />
          <span className="text-xs text-zinc-500">
            [{submission.program.code}] {submission.program.name}
          </span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">
          {submission.title}
        </h1>
        {submission.chapter ? (
          <p className="text-zinc-600 dark:text-zinc-400">
            {submission.chapter}
          </p>
        ) : null}
      </header>

      <EvaluationPanel
        evaluation={evaluation}
        emptyMessage={evaluationEmptyMessage}
      />

      <CitationsPanel
        citations={citations}
        emptyMessage="Aún no se han extraído referencias bibliográficas. Asegúrate de incluir una sección 'Referencias' al final del documento."
      />

      <Card>
        <CardHeader>
          <CardTitle>Subir nueva versión</CardTitle>
          <CardDescription>
            Cada versión se analiza automáticamente. Recibirás una nueva
            evaluación cuando el pipeline termine (típicamente en segundos).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <VersionUploader submissionId={submission.id} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Versiones ({submission.versions.length})</CardTitle>
          <CardDescription>
            Las versiones se ordenan de la más reciente a la más antigua.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <VersionList
            versions={submission.versions}
            downloadBase={`/api/submissions/${submission.id}/versions`}
          />
        </CardContent>
      </Card>
    </div>
  );
}
