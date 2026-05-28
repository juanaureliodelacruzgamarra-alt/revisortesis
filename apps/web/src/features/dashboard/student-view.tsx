"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  submissions: SubmissionSummary[];
  inProgress: number;
  observed: number;
  approved: number;
  recent: SubmissionSummary[];
};

export function StudentView(props: Props) {
  const { t } = useI18n();

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="aurora-page-header-role text-xs font-medium uppercase tracking-widest text-violet-600 dark:text-zinc-500">
          {t("role.student")}
        </p>
        <h1 className="aurora-page-title text-2xl font-semibold tracking-tight text-zinc-900 dark:text-[color:var(--aurora-cream)] sm:text-3xl">
          {t("dash.hello")} {props.userName}
        </h1>
        <p className="aurora-page-desc text-sm text-zinc-600 dark:text-[color:var(--aurora-cream-dim)] sm:text-base">
          {t("student.desc")}
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <KpiCard label={t("student.total_submissions")} value={props.submissions.length} />
        <KpiCard label={t("student.in_progress")} value={props.inProgress} />
        <KpiCard
          label={t("student.observed")}
          value={props.observed}
          tone={props.observed > 0 ? "warning" : "default"}
        />
        <KpiCard label={t("student.approved")} value={props.approved} tone={props.approved > 0 ? "success" : "default"} />
      </section>

      <Card>
        <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{t("student.recent")}</CardTitle>
            <CardDescription>{t("student.recent_desc")}</CardDescription>
          </div>
          <Button asChild size="sm" className="w-full sm:w-auto">
            <Link href="/student/submissions/new">{t("student.new_submission")}</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {props.recent.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("student.no_submissions")}</p>
          ) : (
            <ul className="space-y-2">
              {props.recent.map((s) => (
                <SubmissionRow key={s.id} submission={s} basePath="/student/submissions" />
              ))}
            </ul>
          )}
          {props.submissions.length > props.recent.length ? (
            <p className="mt-3 text-xs text-zinc-500">
              <Link href="/student/submissions" className="underline">
                {t("student.view_all")} ({props.submissions.length}) →
              </Link>
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("student.how_it_works")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-2 text-sm">
            <li><Badge variant="muted">1</Badge> {t("student.step1")}</li>
            <li><Badge variant="muted">2</Badge> {t("student.step2")}</li>
            <li><Badge variant="muted">3</Badge> {t("student.step3")}</li>
            <li><Badge variant="muted">4</Badge> {t("student.step4")}</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
