"use client";

import Link from "next/link";

import { AuthSplit } from "@/features/auth/auth-split";
import { LoginForm } from "@/features/auth/login-form";
import { useI18n } from "@/lib/i18n-provider";

export function LoginPageContent() {
  const { t } = useI18n();

  return (
    <AuthSplit
      pill={t("auth.pill_login")}
      title={
        <>
          {t("auth.login_title_hero")}{" "}
          <span className="aurora-gradient-text">{t("auth.login_title_hero2")}</span>
          <br />
          {t("auth.login_title_hero3")}
        </>
      }
      description={
        <>
          {t("auth.login_desc_hero")}
        </>
      }
      highlights={[
        { label: t("auth.highlight_findings"), value: t("auth.highlight_findings_val") },
        { label: t("auth.highlight_citations"), value: "CrossRef" },
        { label: t("auth.highlight_advisors"), value: "ORCID" },
      ]}
      formTitle={t("auth.login_title")}
      formDescription={t("auth.login_desc")}
      formChildren={<LoginForm />}
      formFooter={
        <>
          {t("auth.no_account")}{" "}
          <Link
            href="/register"
            className="font-medium text-[color:var(--aurora-primary-soft)] underline-offset-4 hover:underline"
          >
            {t("auth.create_one")}
          </Link>
        </>
      }
    />
  );
}
