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
    <div className="flex min-h-screen bg-zinc-50 dark:bg-black">
      <Sidebar user={user} />
      <div className="flex-1 overflow-y-auto">
        <main className="mx-auto w-full max-w-5xl px-8 py-10">{children}</main>
      </div>
    </div>
  );
}
