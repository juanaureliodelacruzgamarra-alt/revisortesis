import { redirect } from "next/navigation";

import { ROLE_HOMES } from "@/lib/auth/types";
import { getSession } from "@/lib/auth/session";

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
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 py-12 dark:bg-black">
      <div className="w-full max-w-md">{children}</div>
    </main>
  );
}
