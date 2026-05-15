import { test as base, expect } from "@playwright/test";

/**
 * KIMY E2E fixtures.
 *
 * Each test gets:
 * - `apiBase`: the KIMY API URL (defaults to localhost:8005)
 * - `studentToken`, `advisorToken`, `adminToken`: pre-registered users created
 *   uniquely per worker so tests don't collide.
 *
 * We register users directly via the API rather than going through the UI in
 * every test — the UI for login is exercised in its own dedicated test.
 */

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? "http://localhost:8005";

type Tokens = { studentToken: string; advisorToken: string; adminToken: string };

async function registerUser(
  role: "student" | "advisor" | "coordinator" | "admin",
): Promise<string> {
  const suffix = Math.random().toString(36).slice(2, 12);
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: `e2e-${role}-${suffix}@test.kimy`,
      password: "E2EPass1234",
      full_name: `E2E ${role}`,
      role,
    }),
  });
  if (!res.ok) {
    throw new Error(`register ${role} failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()).access_token as string;
}

export const test = base.extend<Tokens & { apiBase: string }>({
  apiBase: async ({}, use) => {
    await use(API_BASE);
  },
  studentToken: async ({}, use) => {
    await use(await registerUser("student"));
  },
  advisorToken: async ({}, use) => {
    await use(await registerUser("advisor"));
  },
  adminToken: async ({}, use) => {
    await use(await registerUser("admin"));
  },
});

export { expect };

/** Sets the kimy.access cookie so the page is "logged in" without going through the UI. */
export async function loginAs(
  page: import("@playwright/test").Page,
  token: string,
): Promise<void> {
  await page.context().addCookies([
    {
      name: "kimy.access",
      value: token,
      url: "http://localhost:3000",
      sameSite: "Lax",
    },
  ]);
}
