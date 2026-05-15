import { expect, loginAs, test } from "./fixtures";

test.describe("Role dashboards", () => {
  test("student sees the submissions tab in the sidebar", async ({
    page,
    studentToken,
  }) => {
    await loginAs(page, studentToken);
    await page.goto("/student");
    await expect(page.getByRole("link", { name: /mis avances/i })).toBeVisible();
  });

  test("coordinator dashboard loads KPI cards", async ({ page, apiBase }) => {
    // Need a coordinator token; coordinator endpoints exist but the dashboard
    // calls /stats/overview which is coordinator+admin only.
    const suffix = Math.random().toString(36).slice(2, 10);
    const reg = await fetch(`${apiBase}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: `e2e-coord-${suffix}@test.kimy`,
        password: "Coord12345",
        full_name: "E2E Coord",
        role: "coordinator",
      }),
    });
    expect(reg.status).toBe(201);
    const token = (await reg.json()).access_token;

    await loginAs(page, token);
    await page.goto("/coordinator");
    await expect(
      page.getByRole("heading", { name: /dashboard/i }),
    ).toBeVisible();
    // KPI labels are uppercase via Tailwind tracking — assert by text.
    await expect(page.getByText(/Avances totales/i)).toBeVisible();
  });

  test("admin can reach /admin/fine-tuning", async ({ page, adminToken }) => {
    await loginAs(page, adminToken);
    await page.goto("/admin/fine-tuning");
    // The page heading is an <h1>; the sidebar item is a <Link>, so scope by level.
    await expect(
      page.getByRole("heading", { name: /fine-tuning/i, level: 1 }),
    ).toBeVisible();
    await expect(page.getByText(/Ejemplos elegibles/i)).toBeVisible();
  });

  test("advisor cannot reach /admin/fine-tuning", async ({ page, advisorToken }) => {
    await loginAs(page, advisorToken);
    await page.goto("/admin/fine-tuning");
    // The page-level guard redirects to /advisor.
    await expect(page).toHaveURL(/\/advisor/);
  });
});
