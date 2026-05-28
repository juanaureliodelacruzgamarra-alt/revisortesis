"use client";

import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { registerAction, type AuthActionResult } from "@/lib/auth/actions";
import { type UserRole } from "@/lib/auth/types";
import { useI18n } from "@/lib/i18n-provider";

const ROLE_OPTIONS: UserRole[] = ["student", "advisor", "coordinator"];

export function RegisterForm() {
  const router = useRouter();
  const { t } = useI18n();
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
        <label htmlFor="full_name">
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)]">
            {t("auth.full_name")}
          </span>
        </label>
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
        <label htmlFor="email">
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)]">
            {t("auth.email_label")}
          </span>
        </label>
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
        <label htmlFor="password">
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)]">
            {t("auth.password_label")}
          </span>
        </label>
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
          {t("auth.min_chars")}
        </p>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="role">
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)]">
            {t("auth.role")}
          </span>
        </label>
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
              {t(`role.${role}`)}
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
          t("auth.register_pending")
        ) : (
          <>
            {t("auth.register_btn")}
            <span aria-hidden>→</span>
          </>
        )}
      </button>
    </form>
  );
}
