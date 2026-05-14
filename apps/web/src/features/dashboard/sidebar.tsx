"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { logoutAction } from "@/lib/auth/actions";
import { ROLE_LABELS, type CurrentUser } from "@/lib/auth/types";
import { cn } from "@/lib/cn";
import { NAV_BY_ROLE } from "@/features/dashboard/nav-items";

export function Sidebar({ user }: { user: CurrentUser }) {
  const pathname = usePathname();
  const items = NAV_BY_ROLE[user.role];

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <div className="border-b border-zinc-200 px-6 py-5 dark:border-zinc-800">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Sistema
        </p>
        <p className="text-xl font-semibold tracking-tight">KIMY</p>
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
                "block rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-zinc-900 text-zinc-50 dark:bg-zinc-50 dark:text-zinc-900"
                  : "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-200 p-4 dark:border-zinc-800">
        <p className="truncate text-sm font-medium" title={user.full_name}>
          {user.full_name}
        </p>
        <p className="truncate text-xs text-zinc-500" title={user.email}>
          {user.email}
        </p>
        <p className="mt-1 inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          {ROLE_LABELS[user.role]}
        </p>
        <form action={logoutAction} className="mt-3">
          <Button type="submit" variant="outline" size="sm" className="w-full">
            Cerrar sesión
          </Button>
        </form>
      </div>
    </aside>
  );
}
