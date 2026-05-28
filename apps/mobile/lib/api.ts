import { API_URL } from "@/lib/env";
import { getAccessToken } from "@/lib/storage";
import type {
  AIEvaluation,
  CurrentUser,
  SubmissionDetail,
  SubmissionSummary,
  TokenPair,
} from "@/lib/types";

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message?: string) {
    super(message ?? `API error ${status}`);
    this.status = status;
    this.body = body;
  }
}

type FetchInit = Omit<RequestInit, "body" | "headers"> & {
  body?: unknown;
  authenticated?: boolean;
  headers?: Record<string, string>;
};

export async function apiFetch<T>(path: string, init: FetchInit = {}): Promise<T> {
  const {
    body,
    authenticated = true,
    headers = {},
    method = "GET",
    ...rest
  } = init;

  const finalHeaders: Record<string, string> = { ...headers };
  let payload: BodyInit | undefined;
  if (body !== undefined) {
    payload = JSON.stringify(body);
    finalHeaders["Content-Type"] = "application/json";
  }

  if (authenticated) {
    const token = await getAccessToken();
    if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: finalHeaders,
    body: payload,
    ...rest,
  });

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, parsed);
  }
  return parsed as T;
}

// Auth ----------------------------------------------------------------------

export async function login(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
    authenticated: false,
  });
}

export async function me(): Promise<CurrentUser> {
  return apiFetch<CurrentUser>("/api/v1/auth/me");
}

// Submissions ---------------------------------------------------------------

export async function listSubmissions(): Promise<SubmissionSummary[]> {
  return apiFetch<SubmissionSummary[]>("/api/v1/submissions");
}

export async function getSubmission(id: string): Promise<SubmissionDetail> {
  return apiFetch<SubmissionDetail>(`/api/v1/submissions/${id}`);
}

export async function getEvaluation(
  submissionId: string,
  versionId: string,
): Promise<AIEvaluation | null> {
  try {
    return await apiFetch<AIEvaluation>(
      `/api/v1/submissions/${submissionId}/versions/${versionId}/evaluation`,
    );
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

// Push tokens ---------------------------------------------------------------

export async function registerPushToken(
  expoToken: string,
  deviceLabel?: string,
): Promise<void> {
  await apiFetch("/api/v1/push/register", {
    method: "POST",
    body: { expo_token: expoToken, device_label: deviceLabel ?? null },
  });
}

export async function unregisterPushToken(expoToken: string): Promise<void> {
  await apiFetch(`/api/v1/push/${encodeURIComponent(expoToken)}`, {
    method: "DELETE",
  });
}
