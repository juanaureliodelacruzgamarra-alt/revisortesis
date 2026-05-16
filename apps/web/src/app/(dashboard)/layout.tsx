import { redirect } from "next/navigation";

import { Sidebar } from "@/features/dashboard/sidebar";
import { getCurrentUser } from "@/lib/auth/session";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <div className="dark aurora-app relative isolate flex min-h-screen text-[color:var(--aurora-cream)]">
      <div className="aurora-grid pointer-events-none absolute inset-0 z-0" aria-hidden />
      <div
        className="pointer-events-none absolute left-0 top-0 -z-10 h-[520px] w-[520px] bg-[radial-gradient(circle_at_center,rgba(124,58,237,0.18),transparent_60%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute right-0 bottom-0 -z-10 h-[520px] w-[520px] bg-[radial-gradient(circle_at_center,rgba(196,181,253,0.1),transparent_60%)]"
        aria-hidden
      />
      <Sidebar user={user} />
      <div className="relative z-10 flex-1 overflow-y-auto">
        <main className="mx-auto w-full max-w-5xl px-8 py-10">{children}</main>
      </div>
    </div>
  );
}
