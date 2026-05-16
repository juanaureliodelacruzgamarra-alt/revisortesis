"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, extractErrorMessage } from "@/lib/api/client";
import type { UserRole } from "@/lib/auth/types";

export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type ListFilters = {
  role?: UserRole | null;
  q?: string | null;
  is_active?: boolean | null;
  limit?: number;
};

export async function fetchAdminUsers(
  filters: ListFilters = {},
): Promise<AdminUser[]> {
  const params = new URLSearchParams();
  if (filters.role) params.set("role", filters.role);
  if (filters.q) params.set("q", filters.q);
  if (filters.is_active !== undefined && filters.is_active !== null) {
    params.set("is_active", String(filters.is_active));
  }
  if (filters.limit) params.set("limit", String(filters.limit));
  const qs = params.toString();
  return apiFetch<AdminUser[]>(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
}

export type CreateUserResult =
  | { ok: true; user: AdminUser }
  | { ok: false; error: string };

export async function createAdminUserAction(
  _prev: CreateUserResult | null,
  formData: FormData,
): Promise<CreateUserResult> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const full_name = String(formData.get("full_name") ?? "").trim();
  const role = String(formData.get("role") ?? "student") as UserRole;

  if (!email || !password || !full_name) {
    return { ok: false, error: "Todos los campos son obligatorios." };
  }
  if (password.length < 8) {
    return { ok: false, error: "La contraseña debe tener al menos 8 caracteres." };
  }
  try {
    const user = await apiFetch<AdminUser>("/api/v1/admin/users", {
      method: "POST",
      body: { email, password, full_name, role },
    });
    revalidatePath("/admin/users");
    return { ok: true, user };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo crear el usuario"),
    };
  }
}

export type PatchUserPayload = {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
  password?: string;
};

export async function patchAdminUserAction(
  userId: string,
  payload: PatchUserPayload,
): Promise<{ ok: true } | { ok: false; error: string }> {
  try {
    await apiFetch<AdminUser>(`/api/v1/admin/users/${userId}`, {
      method: "PATCH",
      body: payload,
    });
    revalidatePath("/admin/users");
    return { ok: true };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo actualizar el usuario"),
    };
  }
}
