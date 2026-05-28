"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, extractErrorMessage } from "@/lib/api/client";
import type {
  OrcidAuthorize,
  OrcidLinkResult,
  OrcidPublication,
  OrcidStatus,
} from "@/lib/api/types";

export async function fetchOrcidStatus(): Promise<OrcidStatus> {
  return apiFetch<OrcidStatus>("/api/v1/orcid/me");
}

export async function fetchOrcidPublications(): Promise<OrcidPublication[]> {
  return apiFetch<OrcidPublication[]>("/api/v1/orcid/me/publications");
}

export type StartLinkResult =
  | { ok: true; data: OrcidAuthorize }
  | { ok: false; error: string };

export async function startOrcidLinkAction(): Promise<StartLinkResult> {
  try {
    const data = await apiFetch<OrcidAuthorize>("/api/v1/orcid/authorize", {
      method: "POST",
    });
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo iniciar la vinculación con ORCID"),
    };
  }
}

export type FinishLinkResult =
  | { ok: true; result: OrcidLinkResult }
  | { ok: false; error: string };

export async function finishOrcidLinkAction(
  code: string,
  state: string,
  expectedState: string,
): Promise<FinishLinkResult> {
  try {
    const result = await apiFetch<OrcidLinkResult>("/api/v1/orcid/callback", {
      method: "POST",
      body: { code, state, expected_state: expectedState },
    });
    revalidatePath("/advisor/profile");
    return { ok: true, result };
  } catch (err) {
    return {
      ok: false,
      error: extractErrorMessage(err, "No se pudo completar la vinculación con ORCID"),
    };
  }
}

export async function unlinkOrcidAction(): Promise<void> {
  await apiFetch("/api/v1/orcid/me", { method: "DELETE" });
  revalidatePath("/advisor/profile");
}
