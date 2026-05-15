"use client";

import { useTransition } from "react";

import { assignAdvisorAction } from "@/lib/api/submissions";
import type { AdvisorOption } from "@/lib/api/submissions";

export function AdvisorAssignSelect({
  submissionId,
  currentAdvisorId,
  advisors,
}: {
  submissionId: string;
  currentAdvisorId: string | null;
  advisors: AdvisorOption[];
}) {
  const [pending, start] = useTransition();

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.target.value || null;
    start(async () => {
      await assignAdvisorAction(submissionId, value);
    });
  }

  return (
    <select
      value={currentAdvisorId ?? ""}
      onChange={onChange}
      disabled={pending}
      className="flex h-9 min-w-[14rem] rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950 focus-visible:ring-offset-2 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-950 dark:focus-visible:ring-zinc-300"
    >
      <option value="">— Sin asignar —</option>
      {advisors.map((a) => (
        <option key={a.id} value={a.id}>
          {a.full_name}
          {a.orcid_linked ? "  ·  ORCID" : "  ·  sin ORCID"}
        </option>
      ))}
    </select>
  );
}
