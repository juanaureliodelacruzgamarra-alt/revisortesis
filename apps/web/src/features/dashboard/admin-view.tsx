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
import { useI18n } from "@/lib/i18n-provider";

type Props = {
  userName: string;
  totalUsers: number;
  programsCount: number;
  totalSubmissions: number;
  plagiarismAlerts: number;
  advisorFitAlerts: number;
  usersByRole: Record<string, number>;
  activeModel: string;
  useFineTuned: boolean;
  ftEligible: number;
  ftThreshold: number;
  providerAvailable: boolean;
};

export function AdminView(props: Props) {
  const { t } = useI18n();

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="aurora-page-header-role text-xs font-medium uppercase tracking-widest text-violet-600 dark:text-zinc-500">
          {t("role.admin")}
        </p>
        <h1 className="aurora-page-title text-2xl font-semibold tracking-tight text-zinc-900 dark:text-[color:var(--aurora-cream)] sm:text-3xl">
          {t("dash.hello")} {props.userName}
        </h1>
        <p className="aurora-page-desc text-sm text-zinc-600 dark:text-[color:var(--aurora-cream-dim)] sm:text-base">
          {t("admin.overview")}
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <KpiCard label={t("admin.users")} value={props.totalUsers} helper={`${props.programsCount} ${t("admin.programs_count")}`} />
        <KpiCard label={t("admin.total_submissions")} value={props.totalSubmissions} />
        <KpiCard
          label={t("admin.plagiarism_alerts")}
          value={props.plagiarismAlerts}
          tone={props.plagiarismAlerts > 0 ? "warning" : "default"}
        />
        <KpiCard
          label={t("admin.orcid_alerts")}
          value={props.advisorFitAlerts}
          tone={props.advisorFitAlerts > 0 ? "warning" : "default"}
        />
      </section>

      <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("admin.role_distribution")}</CardTitle>
            <CardDescription>{t("admin.role_dist_desc")}</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {(["student", "advisor", "coordinator", "admin"] as const).map(
                (r) => (
                  <li key={r} className="flex items-center justify-between">
                    <span>{t(`role.${r}`)}</span>
                    <Badge variant="muted">{props.usersByRole[r] ?? 0}</Badge>
                  </li>
                ),
              )}
            </ul>
            <p className="mt-3 text-xs text-zinc-500">
              <Link href="/admin/users" className="underline">
                {t("admin.manage_users")}
              </Link>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("admin.ai_fine_tuning")}</CardTitle>
            <CardDescription>{t("admin.ai_ft_desc")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span>{t("admin.active_model")}</span>
              <Badge variant={props.useFineTuned ? "success" : "muted"}>
                {props.activeModel}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t("admin.feedback_eligible")}</span>
              <Badge variant="muted">
                {props.ftEligible} / {props.ftThreshold}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t("admin.programmatic_tuning")}</span>
              <Badge variant={props.providerAvailable ? "success" : "warning"}>
                {props.providerAvailable ? t("admin.yes") : t("admin.no")}
              </Badge>
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              <Link href="/admin/settings" className="underline">
                {t("admin.adjust_settings")}
              </Link>{" "}
              ·{" "}
              <Link href="/admin/fine-tuning" className="underline">
                {t("admin.view_pipeline")}
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("admin.quick_links")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
            <li><Link href="/admin/users" className="underline">{t("admin.link_users")}</Link></li>
            <li><Link href="/admin/programs" className="underline">{t("admin.link_programs")}</Link></li>
            <li><Link href="/admin/settings" className="underline">{t("admin.link_settings")}</Link></li>
            <li><Link href="/admin/fine-tuning" className="underline">{t("admin.link_pipeline")}</Link></li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
