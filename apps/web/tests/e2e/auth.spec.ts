import { expect, loginAs, test } from "./fixtures";

test.describe("Auth flow", () => {
  test("anonymous user is redirected from /admin to /login", async ({ page }) => {
    const response = await page.goto("/admin", { waitUntil: "domcontentloaded" });
    // The middleware redirects with 307; Playwright follows it.
    expect(page.url()).toContain("/login");
    expect(response?.status()).toBeLessThan(400);
  });

  test("login form submits and redirects to role home", async ({ page, apiBase }) => {
    // Create a fresh student via API so we know the credentials.
    const suffix = Math.random().toString(36).slice(2, 10);
    const email = `e2e-uiflow-${suffix}@test.kimy`;
    const password = "UiFlow12345";
    const registerResp = await fetch(`${apiBase}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        full_name: "UI Flow Student",
        role: "student",
      }),
    });
    expect(registerResp.status).toBe(201);

    // Now log in via the UI.
    await page.goto("/login");
    await page.getByLabel("Correo").fill(email);
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: /ingresar/i }).click();

    await expect(page).toHaveURL(/\/student/);
    await expect(page.getByText(/Hola/i)).toBeVisible();
  });

  test("logged-in student cannot reach /admin pages", async ({ page, studentToken }) => {
    await loginAs(page, studentToken);
    await page.goto("/admin");
    // Middleware lets through (it's not in the matcher when token exists),
    // but the page-level role gate redirects to /student.
    await expect(page).toHaveURL(/\/student/);
  });

  test("logged-in user is bounced from /login to their role home", async ({
    page,
    advisorToken,
  }) => {
    await loginAs(page, advisorToken);
    await page.goto("/login");
    await expect(page).toHaveURL(/\/advisor/);
  });
});
