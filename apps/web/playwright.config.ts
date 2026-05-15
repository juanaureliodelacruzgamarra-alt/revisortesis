import { defineConfig, devices } from "@playwright/test";

/**
 * KIMY web E2E config.
 *
 * The tests assume the API runs on http://localhost:8005 (kimy-up) and the
 * web on http://localhost:3000. Playwright spawns `pnpm dev` itself via
 * `webServer` so CI doesn't have to remember.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false, // serial to share auth state between tests
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    actionTimeout: 5_000,
    navigationTimeout: 10_000,
  },

  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],

  webServer: {
    command: "pnpm --filter @kimy/web dev",
    cwd: "../..",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      NODE_ENV: "test",
    },
  },
});
