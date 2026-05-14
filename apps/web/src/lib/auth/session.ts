import "server-only";

import { decodeJwt } from "jose";

import { readAccessToken } from "@/lib/auth/cookies";
import type { CurrentUser, UserRole } from "@/lib/auth/types";
import { API_URL } from "@/lib/env";

type AccessClaims = {
  sub: string;
  role: UserRole;
  exp: number;
  iat: number;
};

export type Session = {
  userId: string;
  role: UserRole;
  accessToken: string;
};

export async function getSession(): Promise<Session | null> {
  const token = await readAccessToken();
  if (!token) return null;
  try {
    const claims = decodeJwt(token) as AccessClaims;
    if (!claims.sub || !claims.role) return null;
    if (typeof claims.exp === "number" && claims.exp * 1000 < Date.now()) {
      return null;
    }
    return {
      userId: claims.sub,
      role: claims.role,
      accessToken: token,
    };
  } catch {
    return null;
  }
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const session = await getSession();
  if (!session) return null;
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${session.accessToken}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as CurrentUser;
  } catch {
    return null;
  }
}
