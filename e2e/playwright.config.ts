import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E test configuration for Curriculum Curator.
 *
 * Set BASE_URL env var to test against a deployed instance:
 *   BASE_URL=https://curriculumcurator.serveur.au npx playwright test
 *
 * For local development, start backend + frontend first.
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false, // Sequential — tests build on shared DB state
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1, // Single worker — tests are order-dependent
  reporter: [["html", { open: "never" }], ["list"]],

  use: {
    baseURL: process.env.BASE_URL || "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
