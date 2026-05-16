"use client";

import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { registerAction, type AuthActionResult } from "@/lib/auth/actions";
import { ROLE_LABELS, type UserRole } from "@/lib/auth/types";

const ROLE_OPTIONS: UserRole[] = ["student", "advisor", "coordinator"];

function fieldLabel(text: string) {
  return (
    <span className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)]">
      {text}
    </span>
  );
}

export function RegisterForm() {
  const router = useRouter();
  const [state, formAction, pending] = useActionState<
    AuthActionResult | null,
    FormData
  >(registerAction, null);

  useEffect(() => {
    if (state?.ok) {
      router.replace(state.redirectTo);
      router.refresh();
    }
  }, [state, router]);

  return (
    <form action={formAction} className="space-y-5">
      <div className="space-y-1.5">
        <label htmlFor="full_name">{fieldLabel("Nombre completo")}</label>
        <input
          id="full_name"
          name="full_name"
          type="text"
          autoComplete="name"
          minLength={2}
          required
          className="aurora-input flex h-11 w-full rounded-md px-3.5 text-sm"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="email">{fieldLabel("Correo institucional")}</label>
        <input
          id="email"
          name="email"
          type="email"
          placeholder="usuario@unt.edu.pe"
          autoComplete="email"
          required
          className="aurora-input flex h-11 w-full rounded-md px-3.5 text-sm"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="password">{fieldLabel("Contraseña")}</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          required
          className="aurora-input flex h-11 w-full rounded-md px-3.5 text-sm"
        />
        <p className="text-xs text-[color:var(--aurora-cream-dim)]">
          Mínimo 8 caracteres.
        </p>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="role">{fieldLabel("Rol")}</label>
        <select
          id="role"
          name="role"
          defaultValue="student"
          className="aurora-input flex h-11 w-full rounded-md px-3.5 text-sm"
        >
          {ROLE_OPTIONS.map((role) => (
            <option
              key={role}
              value={role}
              className="bg-[color:var(--aurora-base-2)] text-[color:var(--aurora-cream)]"
            >
              {ROLE_LABELS[role]}
            </option>
          ))}
        </select>
      </div>

      {state && !state.ok ? (
        <p className="rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {state.error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="aurora-btn-primary flex h-11 w-full items-center justify-center gap-2 rounded-md text-sm font-semibold tracking-wide disabled:cursor-not-allowed"
      >
        {pending ? (
          "Creando cuenta…"
        ) : (
          <>
            Crear cuenta
            <span aria-hidden>→</span>
          </>
        )}
      </button>
    </form>
  );
}
