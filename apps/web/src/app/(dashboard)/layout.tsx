import { redirect } from "next/navigation";

import { DashboardShell } from "@/features/dashboard/dashboard-shell";
import { Sidebar } from "@/features/dashboard/sidebar";
import { getCurrentUser } from "@/lib/auth/session";
import { Providers } from "./providers";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <Providers>
      <DashboardShell sidebar={<Sidebar user={user} />}>
        {children}
      </DashboardShell>
    </Providers>
  );
}
