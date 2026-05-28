import { redirect } from "next/navigation";

import { getSession } from "@/lib/auth/session";
import { ROLE_HOMES } from "@/lib/auth/types";
import { API_URL } from "@/lib/env";
import { ThemeProvider } from "@/lib/theme-provider";
import { I18nProvider } from "@/lib/i18n-provider";
import { LandingContent } from "@/features/auth/landing-content";

type Health = { status: string; service: string; version: string };

async function fetchHealth(): Promise<Health | null> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as Health;
  } catch {
    return null;
  }
}

export default async function Home() {
  const session = await getSession();
  if (session) redirect(ROLE_HOMES[session.role]);

  const health = await fetchHealth();

  return (
    <ThemeProvider>
      <I18nProvider>
        <LandingContent health={health} />
      </I18nProvider>
    </ThemeProvider>
  );
}
