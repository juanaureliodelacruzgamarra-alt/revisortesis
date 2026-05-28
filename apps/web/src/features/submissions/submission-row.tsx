import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import {
  SubmissionStatusBadge,
  VersionStatusBadge,
} from "@/features/submissions/status-badge";
import type { SubmissionSummary } from "@/lib/api/types";

export function SubmissionRow({
  submission,
  basePath,
  showStudent = false,
}: {
  submission: SubmissionSummary;
  basePath: string;
  showStudent?: boolean;
}) {
  return (
    <li className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <SubmissionStatusBadge status={submission.status} />
            {submission.latest_version_status ? (
              <VersionStatusBadge status={submission.latest_version_status} />
            ) : (
              <Badge variant="outline">Sin versiones</Badge>
            )}
            {submission.latest_version_number ? (
              <Badge variant="muted">v{submission.latest_version_number}</Badge>
            ) : null}
            <Badge variant="outline">[{submission.program.code}]</Badge>
            {submission.advisor_fit_alert ? (
              <Badge variant="destructive" title="La afinidad temática asesor↔tesis es baja">
                ORCID fit {((submission.advisor_fit_score ?? 0) * 100).toFixed(0)}%
              </Badge>
            ) : submission.advisor_fit_score !== null ? (
              <Badge variant="success" title="Buena afinidad asesor↔tesis">
                ORCID fit {(submission.advisor_fit_score * 100).toFixed(0)}%
              </Badge>
            ) : null}
          </div>
          <Link
            href={`${basePath}/${submission.id}`}
            className="mt-2 block truncate text-base font-medium hover:underline"
            title={submission.title}
          >
            {submission.title}
            {submission.chapter ? (
              <span className="ml-2 text-sm font-normal text-zinc-500">
                · {submission.chapter}
              </span>
            ) : null}
          </Link>
          {showStudent ? (
            <p className="truncate text-xs text-zinc-500">
              {submission.student.full_name} · {submission.student.email}
            </p>
          ) : (
            <p className="text-xs text-zinc-500">
              Creado{" "}
              {new Date(submission.created_at).toLocaleDateString("es-PE")}
            </p>
          )}
        </div>
      </div>
    </li>
  );
}
