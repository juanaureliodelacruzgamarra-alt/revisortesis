"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { logoutAction } from "@/lib/auth/actions";
import { ROLE_LABELS, type CurrentUser } from "@/lib/auth/types";
import { cn } from "@/lib/cn";
import { NAV_BY_ROLE } from "@/features/dashboard/nav-items";
import { useTheme } from "@/lib/theme-provider";
import { useI18n } from "@/lib/i18n-provider";

export function Sidebar({ user }: { user: CurrentUser }) {
  const pathname = usePathname();
  const items = NAV_BY_ROLE[user.role];
  const { theme, toggle } = useTheme();
  const { lang, setLang, t } = useI18n();

  return (
    <aside className="relative z-10 flex h-screen w-64 flex-col border-r border-[color:rgba(196,181,253,0.12)] bg-[rgba(7,9,29,0.7)] backdrop-blur-xl">
      <div className="border-b border-[color:rgba(196,181,253,0.1)] px-6 py-5">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-violet-500 to-violet-300 text-xs font-bold text-zinc-950 shadow-[0_0_18px_-4px_rgba(124,58,237,0.6)]">
            A
          </span>
          <p className="aurora-display text-xl font-semibold tracking-tight text-[color:var(--aurora-cream)]">
            Aurelio
          </p>
        </div>
        <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.22em] text-[color:var(--aurora-cream-dim)]">
          {t("sidebar.title")}
        </p>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {items.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative block rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-gradient-to-r from-violet-600/40 to-violet-400/10 text-[color:var(--aurora-cream)] shadow-[0_0_0_1px_rgba(196,181,253,0.25)_inset]"
                  : "text-[color:var(--aurora-cream-dim)] hover:bg-[rgba(124,58,237,0.12)] hover:text-[color:var(--aurora-cream)]",
              )}
            >
              {active ? (
                <span
                  aria-hidden
                  className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r bg-gradient-to-b from-violet-300 to-violet-500"
                />
              ) : null}
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Theme + Language toggles */}
      <div className="flex items-center gap-2 border-t border-[color:rgba(196,181,253,0.1)] px-4 py-3">
        <button
          onClick={toggle}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-[color:rgba(196,181,253,0.25)] bg-[rgba(124,58,237,0.12)] px-2 py-1.5 text-[11px] font-medium uppercase tracking-wider text-[color:var(--aurora-cream-dim)] transition-colors hover:bg-[rgba(124,58,237,0.25)] hover:text-[color:var(--aurora-cream)]"
          title={theme === "dark" ? t("theme.light") : t("theme.dark")}
        >
          {theme === "dark" ? "☀️" : "🌙"}
          <span>{theme === "dark" ? t("theme.light") : t("theme.dark")}</span>
        </button>
        <button
          onClick={() => setLang(lang === "es" ? "en" : "es")}
          className="flex items-center justify-center gap-1.5 rounded-md border border-[color:rgba(196,181,253,0.25)] bg-[rgba(124,58,237,0.12)] px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider text-[color:var(--aurora-cream-dim)] transition-colors hover:bg-[rgba(124,58,237,0.25)] hover:text-[color:var(--aurora-cream)]"
          title={lang === "es" ? "English" : "Español"}
        >
          {lang === "es" ? "🇬🇧 EN" : "🇪🇸 ES"}
        </button>
      </div>

      <div className="border-t border-[color:rgba(196,181,253,0.1)] p-4">
        <p
          className="truncate text-sm font-medium text-[color:var(--aurora-cream)]"
          title={user.full_name}
        >
          {user.full_name}
        </p>
        <p
          className="truncate text-xs text-[color:var(--aurora-cream-dim)]"
          title={user.email}
        >
          {user.email}
        </p>
        <p className="mt-2 inline-flex items-center rounded-full border border-[color:rgba(196,181,253,0.25)] bg-[rgba(124,58,237,0.12)] px-2 py-0.5 text-[10px] font-medium uppercase tracking-widest text-[color:var(--aurora-primary-soft)]">
          {ROLE_LABELS[user.role]}
        </p>
        <form action={logoutAction} className="mt-3">
          <button
            type="submit"
            className="aurora-btn-ghost flex h-9 w-full items-center justify-center rounded-md text-xs font-medium uppercase tracking-widest"
          >
            {t("sidebar.logout")}
          </button>
        </form>
      </div>
    </aside>
  );
}
