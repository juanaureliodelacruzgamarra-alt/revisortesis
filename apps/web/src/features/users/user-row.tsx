"use client";

import { useState, useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { patchAdminUserAction, type AdminUser } from "@/lib/api/users";
import { ROLE_LABELS, type UserRole } from "@/lib/auth/types";

const ROLES: UserRole[] = ["student", "advisor", "coordinator", "admin"];

function roleVariant(role: UserRole) {
  switch (role) {
    case "admin":
      return "destructive" as const;
    case "coordinator":
      return "warning" as const;
    case "advisor":
      return "success" as const;
    default:
      return "muted" as const;
  }
}

export function UserRow({
  user,
  currentUserId,
}: {
  user: AdminUser;
  currentUserId: string;
}) {
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const isSelf = user.id === currentUserId;

  function update(payload: Parameters<typeof patchAdminUserAction>[1]) {
    setError(null);
    start(async () => {
      const r = await patchAdminUserAction(user.id, payload);
      if (!r.ok) setError(r.error);
    });
  }

  function onRoleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const next = e.target.value as UserRole;
    if (next === user.role) return;
    update({ role: next });
  }

  function onToggleActive() {
    update({ is_active: !user.is_active });
  }

  function onResetPassword() {
    const pwd = prompt(
      `Nueva contraseña para ${user.email} (mín. 8 caracteres):`,
    );
    if (!pwd) return;
    if (pwd.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    update({ password: pwd });
  }

  return (
    <li className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)] sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate font-medium" title={user.email}>
            {user.full_name}
          </span>
          <Badge variant={roleVariant(user.role)}>{ROLE_LABELS[user.role]}</Badge>
          {!user.is_active ? (
            <Badge variant="muted">Inactivo</Badge>
          ) : null}
          {isSelf ? <Badge variant="outline">tú</Badge> : null}
        </div>
        <p className="mt-1 truncate text-xs text-zinc-500" title={user.email}>
          {user.email} · creado{" "}
          {new Date(user.created_at).toLocaleDateString("es-PE")}
        </p>
        {error ? (
          <p className="mt-1 text-xs text-rose-600 dark:text-rose-400">
            {error}
          </p>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={user.role}
          onChange={onRoleChange}
          disabled={pending || isSelf}
          className="h-9 rounded-md border border-zinc-200 bg-white px-2 text-sm dark:border-[color:rgba(196,181,253,0.12)] dark:bg-[rgba(11,14,42,0.55)] disabled:opacity-50"
          title={isSelf ? "No puedes cambiar tu propio rol" : undefined}
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABELS[r]}
            </option>
          ))}
        </select>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onToggleActive}
          disabled={pending || isSelf}
          title={isSelf ? "No puedes desactivarte" : undefined}
        >
          {user.is_active ? "Desactivar" : "Activar"}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onResetPassword}
          disabled={pending}
        >
          Resetear clave
        </Button>
      </div>
    </li>
  );
}
