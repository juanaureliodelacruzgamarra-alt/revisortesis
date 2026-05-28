"use client";

import Link from "next/link";

import { AuthSplit } from "@/features/auth/auth-split";
import { RegisterForm } from "@/features/auth/register-form";
import { useI18n } from "@/lib/i18n-provider";

export function RegisterPageContent() {
  const { t } = useI18n();

  return (
    <AuthSplit
      pill={t("auth.pill_register")}
      title={
        <>
          {t("auth.register_title_hero1")} <br />
          <span className="aurora-gradient-text">{t("auth.register_title_hero2")}</span>{" "}
          {t("auth.register_title_hero3")}
        </>
      }
      description={
        <>
          {t("auth.register_desc_hero")}
        </>
      }
      highlights={[
        { label: t("auth.highlight_structure"), value: "APA 7" },
        { label: t("auth.highlight_plagiarism"), value: "pgvector" },
        { label: t("auth.highlight_roles"), value: "4" },
      ]}
      formTitle={t("auth.register_title")}
      formDescription={t("auth.register_desc")}
      formChildren={<RegisterForm />}
      formFooter={
        <>
          {t("auth.have_account")}{" "}
          <Link
            href="/login"
            className="font-medium text-[color:var(--aurora-primary-soft)] underline-offset-4 hover:underline"
          >
            {t("auth.sign_in")}
          </Link>
        </>
      }
    />
  );
}
