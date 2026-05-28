import { redirect } from "next/navigation";

import { ROLE_HOMES } from "@/lib/auth/types";
import { getSession } from "@/lib/auth/session";
import { ThemeProvider } from "@/lib/theme-provider";
import { I18nProvider } from "@/lib/i18n-provider";
import { AuthHeader, AuthFooter } from "@/features/auth/auth-header";

export default async function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();
  if (session) {
    redirect(ROLE_HOMES[session.role]);
  }

  return (
    <ThemeProvider>
      <I18nProvider>
        <main className="dark aurora-shell relative isolate min-h-screen overflow-hidden">
          <div className="aurora-grid absolute inset-0 z-0" aria-hidden />
          <div
            className="absolute inset-x-0 top-0 -z-10 h-[60vh] bg-[radial-gradient(circle_at_20%_20%,rgba(124,58,237,0.35),transparent_55%)]"
            aria-hidden
          />
          <div
            className="absolute inset-x-0 bottom-0 -z-10 h-[60vh] bg-[radial-gradient(circle_at_90%_85%,rgba(196,181,253,0.18),transparent_55%)]"
            aria-hidden
          />
          <div className="relative z-10 mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <AuthHeader />

            <div className="flex flex-1 items-center justify-center py-6 sm:py-10 lg:py-16">
              {children}
            </div>

            <AuthFooter />
          </div>
        </main>
      </I18nProvider>
    </ThemeProvider>
  );
}
