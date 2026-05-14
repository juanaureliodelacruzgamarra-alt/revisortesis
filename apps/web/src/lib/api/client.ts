import "server-only";

import { readAccessToken } from "@/lib/auth/cookies";
import { API_URL } from "@/lib/env";

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message?: string) {
    super(message ?? `API error ${status}`);
    this.status = status;
    this.body = body;
  }
}

type ApiInit = Omit<RequestInit, "body" | "headers"> & {
  body?: unknown;          // JSON-serializable
  formData?: FormData;     // for multipart uploads (skips JSON)
  headers?: Record<string, string>;
  authenticated?: boolean; // defaults true
};

export async function apiFetch<T = unknown>(
  path: string,
  init: ApiInit = {},
): Promise<T> {
  const {
    body,
    formData,
    headers = {},
    authenticated = true,
    method = "GET",
    cache = "no-store",
    ...rest
  } = init;

  const finalHeaders: Record<string, string> = { ...headers };
  let payload: BodyInit | undefined;

  if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    finalHeaders["Content-Type"] = "application/json";
  }

  if (authenticated) {
    const token = await readAccessToken();
    if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: finalHeaders,
    body: payload,
    cache,
    ...rest,
  });

  if (res.status === 204) return undefined as T;

  let parsed: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, parsed);
  }
  return parsed as T;
}

export function extractErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError) {
    const body = err.body as { detail?: string | Array<{ msg?: string }> } | null;
    if (body) {
      if (typeof body.detail === "string") return body.detail;
      if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        return body.detail[0].msg;
      }
    }
    return `${fallback} (HTTP ${err.status})`;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
