"use client";

import { useI18n } from "@/lib/i18n-provider";
import { useTheme } from "@/lib/theme-provider";

export function AuthHeader() {
  const { t, lang, setLang } = useI18n();
  const { theme, toggle } = useTheme();

  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-violet-500 to-violet-300 text-sm font-bold text-zinc-950 shadow-[0_0_30px_-6px_rgba(124,58,237,0.7)]">
          A
        </span>
        <span className="aurora-display text-lg font-semibold tracking-tight text-[color:var(--aurora-cream)]">
          Aurelio
        </span>
      </div>
      <div className="flex items-center gap-3">
        <nav className="hidden items-center gap-6 text-xs uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)] sm:flex">
          <span>{t("auth.nav_review")}</span>
          <span>{t("auth.nav_evidence")}</span>
          <span>{t("auth.nav_rigor")}</span>
        </nav>
        <button
          onClick={toggle}
          className="flex h-8 w-8 items-center justify-center rounded-full border border-[color:rgba(196,181,253,0.3)] text-sm transition hover:bg-[color:rgba(124,58,237,0.15)]"
          title={theme === "dark" ? t("theme.light") : t("theme.dark")}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
        <button
          onClick={() => setLang(lang === "es" ? "en" : "es")}
          className="flex h-8 items-center justify-center rounded-full border border-[color:rgba(196,181,253,0.3)] px-2.5 text-[11px] font-medium uppercase tracking-wider text-[color:var(--aurora-cream-dim)] transition hover:bg-[color:rgba(124,58,237,0.15)]"
          title={lang === "es" ? "English" : "Español"}
        >
          {lang === "es" ? "🇬🇧 EN" : "🇪🇸 ES"}
        </button>
      </div>
    </header>
  );
}

export function AuthFooter() {
  const { t } = useI18n();

  return (
    <footer className="flex flex-col items-center justify-between gap-2 text-[10px] uppercase tracking-[0.2em] text-[color:var(--aurora-cream-dim)] sm:flex-row">
      <span>{t("auth.footer_university")}</span>
      <span>{t("auth.footer_version")}</span>
    </footer>
  );
}
