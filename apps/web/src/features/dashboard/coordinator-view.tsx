"use client";

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
import { ProgramBars } from "@/features/dashboard/program-bars";
import { StatusDonut } from "@/features/dashboard/status-donut";
import { useI18n } from "@/lib/i18n-provider";
import type { ProgramGrade } from "@/lib/api/stats";

type ActivityItem = {
  submission_id: string;
  submission_title: string;
  actor_name: string;
  description: string;
  kind: string;
  occurred_at: string;
};

type Props = {
  totalSubmissions: number;
  avgAiGrade: number | null;
  avgAiPercentage: number | null;
  aiHumanConcordance: number | null;
  advisorsWithOrcid: number;
  plagiarismAlerts: number;
  advisorFitAlerts: number;
  lowCompliance: number;
  citationsProblematic: number;
  citationsTotal: number;
  submissionsByStatus: { status: string; count: number }[];
  gradesPerProgram: ProgramGrade[];
  activity: ActivityItem[];
};

function formatPct(v: number | null) {
  return v === null ? "—" : `${v.toFixed(1)}%`;
}
function formatGrade(v: number | null) {
  return v === null ? "—" : v.toFixed(2);
}

export function CoordinatorView(props: Props) {
  const { t } = useI18n();

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-2xl space-y-1">
          <p className="aurora-page-header-role text-xs font-medium uppercase tracking-widest text-violet-600 dark:text-zinc-500">
            {t("coord.title")}
          </p>
          <h1 className="aurora-page-title text-2xl font-semibold tracking-tight text-zinc-900 dark:text-[color:var(--aurora-cream)] sm:text-3xl">
            {t("nav.dashboard")}
          </h1>
          <p className="aurora-page-desc text-sm text-zinc-600 dark:text-[color:var(--aurora-cream-dim)] sm:text-base">
            {t("coord.desc")}
          </p>
        </div>
        <Button asChild size="lg" className="w-full sm:w-auto">
          <a href="/api/reports/executive.pdf" target="_blank" rel="noopener noreferrer">
            {t("coord.exec_report")}
          </a>
        </Button>
      </header>

      <section className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <KpiCard label={t("admin.total_submissions")} value={props.totalSubmissions} />
        <KpiCard
          label={t("coord.avg_ai_grade")}
          value={formatGrade(props.avgAiGrade)}
          helper={`/ 20 · ${formatPct(props.avgAiPercentage)} ${t("coord.compliance")}`}
        />
        <KpiCard
          label={t("coord.ai_human_concordance")}
          value={formatPct(props.aiHumanConcordance)}
          helper={t("coord.concordance_helper")}
        />
        <KpiCard label={t("coord.advisors_orcid")} value={props.advisorsWithOrcid} />
        <KpiCard
          label={t("coord.plagiarism_alerts")}
          value={props.plagiarismAlerts}
          tone={props.plagiarismAlerts > 0 ? "danger" : "default"}
          helper={t("coord.plagiarism_helper")}
        />
        <KpiCard
          label={t("coord.orcid_fit_alerts")}
          value={props.advisorFitAlerts}
          tone={props.advisorFitAlerts > 0 ? "warning" : "default"}
          helper={t("coord.orcid_fit_helper")}
        />
        <KpiCard
          label={t("coord.low_compliance")}
          value={props.lowCompliance}
          tone={props.lowCompliance > 0 ? "warning" : "default"}
          helper={t("coord.low_compliance_helper")}
        />
        <KpiCard
          label={t("coord.problematic_citations")}
          value={props.citationsProblematic}
          helper={`${t("coord.citations_of")} ${props.citationsTotal} ${t("coord.citations_extracted")}`}
          tone={props.citationsProblematic > 0 ? "warning" : "default"}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("coord.status_distribution")}</CardTitle>
            <CardDescription>{t("coord.status_dist_desc")}</CardDescription>
          </CardHeader>
          <CardContent>
            <StatusDonut data={props.submissionsByStatus} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("coord.avg_grade_program")}</CardTitle>
            <CardDescription>{t("coord.avg_grade_desc")}</CardDescription>
          </CardHeader>
          <CardContent>
            <ProgramBars data={props.gradesPerProgram} />
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>{t("coord.recent_activity")}</CardTitle>
          <CardDescription>
            {t("coord.recent_events")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {props.activity.length === 0 ? (
            <p className="text-sm text-zinc-500">{t("coord.no_activity")}</p>
          ) : (
            <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {props.activity.map((a, idx) => (
                <li
                  key={`${a.submission_id}-${a.occurred_at}-${idx}`}
                  className="flex flex-col gap-2 py-3 text-sm sm:flex-row sm:items-start sm:justify-between sm:gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-zinc-900 dark:text-[color:var(--aurora-cream)]">
                      {a.description}
                    </p>
                    <p className="truncate text-xs text-zinc-500">
                      {a.submission_title} · {a.actor_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 sm:flex-col sm:items-end sm:gap-1">
                    <Badge variant="outline" className="font-mono text-xs">
                      {a.kind.replace(/_/g, " ")}
                    </Badge>
                    <span className="text-xs text-zinc-500">
                      {new Date(a.occurred_at).toLocaleString("es-PE")}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
