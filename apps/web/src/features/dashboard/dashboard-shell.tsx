"use client";

import { useState, type ReactNode } from "react";
import { useI18n } from "@/lib/i18n-provider";

export function DashboardShell({
  sidebar,
  children,
}: {
  sidebar: ReactNode;
  children: ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { t } = useI18n();

  return (
    <div className="aurora-app relative isolate flex min-h-screen">
      <div className="aurora-grid pointer-events-none absolute inset-0 z-0" aria-hidden />
      <div
        className="aurora-glow-blob pointer-events-none absolute left-0 top-0 -z-10 h-[520px] w-[520px] bg-[radial-gradient(circle_at_center,rgba(124,58,237,0.18),transparent_60%)]"
        aria-hidden
      />
      <div
        className="aurora-glow-blob pointer-events-none absolute right-0 bottom-0 -z-10 h-[520px] w-[520px] bg-[radial-gradient(circle_at_center,rgba(196,181,253,0.1),transparent_60%)]"
        aria-hidden
      />

      {/* Mobile hamburger button */}
      <button
        type="button"
        onClick={() => setSidebarOpen(true)}
        className="fixed left-4 top-4 z-50 flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 bg-white/90 shadow-md backdrop-blur-sm dark:border-[color:rgba(196,181,253,0.25)] dark:bg-[rgba(11,14,42,0.85)] md:hidden"
        aria-label={t("sidebar.menu")}
      >
        <svg className="h-5 w-5 text-zinc-700 dark:text-[color:var(--aurora-cream)]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay fixed inset-0 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden
        />
      )}

      {/* Sidebar — hidden on mobile, slide-in when open */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 transform transition-transform duration-200 ease-in-out md:relative md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Mobile close button */}
        <button
          type="button"
          onClick={() => setSidebarOpen(false)}
          className="absolute right-3 top-3 z-50 flex h-8 w-8 items-center justify-center rounded-md text-zinc-500 hover:text-zinc-700 dark:text-[color:var(--aurora-cream-dim)] dark:hover:text-[color:var(--aurora-cream)] md:hidden"
          aria-label={t("sidebar.close")}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        {sidebar}
      </div>

      {/* Main content */}
      <div className="relative z-10 flex-1 overflow-y-auto">
        <main className="mx-auto w-full max-w-5xl px-4 py-6 pt-16 md:px-8 md:py-10 md:pt-10">
          {children}
        </main>
      </div>
    </div>
  );
}
