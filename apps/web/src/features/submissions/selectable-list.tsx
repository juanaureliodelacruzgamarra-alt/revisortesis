"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { AdvisorAssignSelect } from "@/features/submissions/advisor-assign-select";
import { BulkToolbar } from "@/features/submissions/bulk-toolbar";
import {
  SubmissionStatusBadge,
  VersionStatusBadge,
} from "@/features/submissions/status-badge";
import type { AdvisorOption } from "@/lib/api/submissions";
import type { SubmissionSummary } from "@/lib/api/types";

export function SelectableSubmissionsList({
  submissions,
  advisors,
}: {
  submissions: SubmissionSummary[];
  advisors: AdvisorOption[];
}) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const allChecked = useMemo(
    () => submissions.length > 0 && selected.size === submissions.length,
    [submissions, selected],
  );

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (allChecked) setSelected(new Set());
    else setSelected(new Set(submissions.map((s) => s.id)));
  }

  return (
    <div className="space-y-4">
      <BulkToolbar
        selectedIds={Array.from(selected)}
        onClear={() => setSelected(new Set())}
        advisors={advisors}
      />

      <div className="flex items-center justify-between text-xs text-zinc-500">
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={allChecked}
            onChange={toggleAll}
            disabled={submissions.length === 0}
          />
          Seleccionar todos ({submissions.length})
        </label>
      </div>

      <ul className="space-y-3">
        {submissions.map((s) => {
          const checked = selected.has(s.id);
          return (
            <li
              key={s.id}
              className={`rounded-lg border p-4 transition-colors ${
                checked
                  ? "border-zinc-900 bg-zinc-50 dark:border-zinc-50 dark:bg-zinc-900"
                  : "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
              }`}
            >
              <div className="flex flex-wrap items-start gap-3">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(s.id)}
                  className="mt-1"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <SubmissionStatusBadge status={s.status} />
                    {s.latest_version_status ? (
                      <VersionStatusBadge status={s.latest_version_status} />
                    ) : (
                      <Badge variant="outline">Sin versiones</Badge>
                    )}
                    {s.latest_version_number ? (
                      <Badge variant="muted">v{s.latest_version_number}</Badge>
                    ) : null}
                    <Badge variant="outline">[{s.program.code}]</Badge>
                    {s.advisor_fit_alert ? (
                      <Badge variant="destructive">
                        ORCID fit {((s.advisor_fit_score ?? 0) * 100).toFixed(0)}%
                      </Badge>
                    ) : s.advisor_fit_score !== null ? (
                      <Badge variant="success">
                        ORCID fit {(s.advisor_fit_score * 100).toFixed(0)}%
                      </Badge>
                    ) : null}
                  </div>
                  <Link
                    href={`/advisor/reviews/${s.id}`}
                    className="mt-2 block truncate text-base font-medium hover:underline"
                    title={s.title}
                  >
                    {s.title}
                    {s.chapter ? (
                      <span className="ml-2 text-sm font-normal text-zinc-500">
                        · {s.chapter}
                      </span>
                    ) : null}
                  </Link>
                  <p className="truncate text-xs text-zinc-500">
                    {s.student.full_name} · {s.student.email}
                  </p>
                </div>

                <div className="flex flex-col items-end gap-2">
                  <AdvisorAssignSelect
                    submissionId={s.id}
                    currentAdvisorId={s.advisor_id}
                    advisors={advisors}
                  />
                  <a
                    href={`/api/submissions/${s.id}/report.pdf`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
                  >
                    Descargar acta PDF →
                  </a>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
