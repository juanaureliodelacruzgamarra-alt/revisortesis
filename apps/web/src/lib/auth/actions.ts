"use server";

import { redirect } from "next/navigation";

import { clearAuthCookies, setAuthCookies } from "@/lib/auth/cookies";
import {
  ROLE_HOMES,
  type LoginPayload,
  type RegisterPayload,
  type TokenPair,
  type UserRole,
} from "@/lib/auth/types";
import { API_URL } from "@/lib/env";

export type AuthActionResult =
  | { ok: true; role: UserRole; redirectTo: string }
  | { ok: false; error: string };

async function callAuthEndpoint(
  endpoint: "/api/v1/auth/login" | "/api/v1/auth/register",
  body: LoginPayload | RegisterPayload,
): Promise<AuthActionResult> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    return { ok: false, error: "No se pudo contactar el servidor" };
  }

  if (!res.ok) {
    let detail = "Error en la autenticación";
    try {
      const data = (await res.json()) as { detail?: string | unknown[] };
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) {
        const first = data.detail[0] as { msg?: string } | undefined;
        if (first?.msg) detail = first.msg;
      }
    } catch {
      // fall through
    }
    return { ok: false, error: detail };
  }

  const tokens = (await res.json()) as TokenPair;
  await setAuthCookies(tokens.access_token, tokens.refresh_token);

  const meRes = await fetch(`${API_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
    cache: "no-store",
  });
  if (!meRes.ok) {
    return { ok: false, error: "No se pudo cargar el perfil" };
  }
  const me = (await meRes.json()) as { role: UserRole };
  return { ok: true, role: me.role, redirectTo: ROLE_HOMES[me.role] };
}

export async function loginAction(
  _state: AuthActionResult | null,
  formData: FormData,
): Promise<AuthActionResult> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) {
    return { ok: false, error: "Email y contraseña son requeridos" };
  }
  return callAuthEndpoint("/api/v1/auth/login", { email, password });
}

export async function registerAction(
  _state: AuthActionResult | null,
  formData: FormData,
): Promise<AuthActionResult> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const fullName = String(formData.get("full_name") ?? "").trim();
  const role = (String(formData.get("role") ?? "student") as UserRole) || "student";

  if (!email || !password || !fullName) {
    return { ok: false, error: "Todos los campos son requeridos" };
  }
  if (password.length < 8) {
    return { ok: false, error: "La contraseña debe tener al menos 8 caracteres" };
  }

  return callAuthEndpoint("/api/v1/auth/register", {
    email,
    password,
    full_name: fullName,
    role,
  });
}

export async function logoutAction() {
  await clearAuthCookies();
  redirect("/login");
}
