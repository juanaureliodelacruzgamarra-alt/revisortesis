"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n-provider";
import { useTheme } from "@/lib/theme-provider";

type Health = { status: string; service: string; version: string };

export function LandingContent({ health }: { health: Health | null }) {
  const { t, lang, setLang } = useI18n();
  const { theme, toggle } = useTheme();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 px-4 py-12 dark:bg-black sm:px-6 sm:py-16">
      {/* Theme + Lang toggles */}
      <div className="fixed right-4 top-4 z-50 flex items-center gap-2">
        <button
          onClick={toggle}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-200 bg-white/90 shadow-sm transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800/90 dark:hover:bg-zinc-700"
          title={theme === "dark" ? t("theme.light") : t("theme.dark")}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
        <button
          onClick={() => setLang(lang === "es" ? "en" : "es")}
          className="flex h-9 items-center justify-center rounded-lg border border-zinc-200 bg-white/90 px-2.5 text-[11px] font-medium uppercase tracking-wider text-zinc-600 shadow-sm transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800/90 dark:text-zinc-300 dark:hover:bg-zinc-700"
          title={lang === "es" ? "English" : "Español"}
        >
          {lang === "es" ? "🇬🇧 EN" : "🇪🇸 ES"}
        </button>
      </div>

      <div className="w-full max-w-2xl space-y-8">
        <header className="space-y-2 text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-zinc-500">
            {t("landing.platform")}
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-[color:var(--aurora-cream)] sm:text-4xl">
            {t("landing.title")}
          </h1>
          <p className="mx-auto max-w-xl text-sm text-zinc-600 dark:text-[color:var(--aurora-cream-dim)] sm:text-base">
            {t("landing.description")}
          </p>
        </header>

        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Button asChild className="w-full sm:w-auto">
            <Link href="/login">{t("landing.login")}</Link>
          </Button>
          <Button asChild variant="outline" className="w-full sm:w-auto">
            <Link href="/register">{t("landing.register")}</Link>
          </Button>
        </div>

        <div className="flex justify-center">
          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
              health
                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                : "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                health ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            API {health ? `${health.service} v${health.version}` : "offline"}
          </span>
        </div>
      </div>
    </main>
  );
}
