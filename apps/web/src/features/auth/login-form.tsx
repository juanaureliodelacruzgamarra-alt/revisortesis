"use client";

import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { loginAction, type AuthActionResult } from "@/lib/auth/actions";
import { useI18n } from "@/lib/i18n-provider";

export function LoginForm() {
  const router = useRouter();
  const { t } = useI18n();
  const [state, formAction, pending] = useActionState<
    AuthActionResult | null,
    FormData
  >(loginAction, null);

  useEffect(() => {
    if (state?.ok) {
      router.replace(state.redirectTo);
      router.refresh();
    }
  }, [state, router]);

  return (
    <form action={formAction} className="space-y-5">
      <div className="space-y-1.5">
        <label
          htmlFor="email"
          className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)]"
        >
          {t("auth.email_label")}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          placeholder="alumno@unt.edu.pe"
          autoComplete="email"
          required
          className="aurora-input flex h-11 w-full rounded-md px-3.5 text-sm"
        />
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="password"
          className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--aurora-cream-dim)]"
        >
          {t("auth.password_label")}
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="aurora-input flex h-11 w-full rounded-md px-3.5 text-sm"
        />
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
          t("auth.login_pending")
        ) : (
          <>
            {t("auth.login_btn")}
            <span aria-hidden>→</span>
          </>
        )}
      </button>
    </form>
  );
}
