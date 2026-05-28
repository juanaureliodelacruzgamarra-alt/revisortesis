"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { KpiCard } from "@/features/dashboard/kpi-card";
import { SubmissionRow } from "@/features/submissions/submission-row";
import { useI18n } from "@/lib/i18n-provider";
import type { SubmissionSummary } from "@/lib/api/types";

type Props = {
  userName: string;
  totalReviews: number;
  pending: number;
  approved: number;
  fitAlerts: number;
  upcoming: SubmissionSummary[];
};

export function AdvisorView(props: Props) {
  const { t } = useI18n();

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="aurora-page-header-role text-xs font-medium uppercase tracking-widest text-violet-600 dark:text-zinc-500">
          {t("role.advisor")}
        </p>
        <h1 className="aurora-page-title text-2xl font-semibold tracking-tight text-zinc-900 dark:text-[color:var(--aurora-cream)] sm:text-3xl">
          {t("dash.hello")} {props.userName}
        </h1>
        <p className="aurora-page-desc text-sm text-zinc-600 dark:text-[color:var(--aurora-cream-dim)] sm:text-base">
          {t("advisor.desc")}
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <KpiCard label={t("advisor.assigned")} value={props.totalReviews} />
        <KpiCard label={t("advisor.pending")} value={props.pending} tone={props.pending > 0 ? "warning" : "default"} />
        <KpiCard label={t("student.approved")} value={props.approved} tone={props.approved > 0 ? "success" : "default"} />
        <KpiCard
          label={t("advisor.orcid_fit_alert")}
          value={props.fitAlerts}
          tone={props.fitAlerts > 0 ? "warning" : "default"}
          helper={t("advisor.affinity_helper")}
        />
      </section>

      <Card>
        <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{t("advisor.to_review")}</CardTitle>
            <CardDescription>{t("advisor.to_review_desc")}</CardDescription>
          </div>
          <Badge variant="muted">{props.upcoming.length}</Badge>
        </CardHeader>
        <CardContent>
          {props.upcoming.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("advisor.no_pending")}</p>
          ) : (
            <ul className="space-y-2">
              {props.upcoming.map((s) => (
                <SubmissionRow key={s.id} submission={s} basePath="/advisor/reviews" showStudent />
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-zinc-500">
            <Link href="/advisor/reviews" className="underline">
              {t("advisor.view_all_reviews")}
            </Link>{" "}
            ·{" "}
            <Link href="/advisor/profile" className="underline">
              {t("advisor.my_orcid_profile")}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
