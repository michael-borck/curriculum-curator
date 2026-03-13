/**
 * Auth helpers for E2E tests.
 */

import { type Page, expect } from "@playwright/test";
import { ADMIN_USER, REGULAR_USER } from "./constants.js";
import { ensureUsers } from "./setup.js";

/**
 * Dismiss the welcome onboarding modal if visible.
 * The onboarding has a 500ms delay before appearing and may show on any page
 * for users without educationSector/teachingStyle set.
 */
export async function dismissOnboarding(page: Page): Promise<void> {
  // Wait for the 500ms delay the app uses before showing onboarding
  await page.waitForTimeout(800);
  // Target specifically the onboarding overlay by its "Skip for now" or "Welcome" content
  const skipBtn = page.getByText("Skip for now");
  if (await skipBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
    await skipBtn.click();
    await skipBtn.waitFor({ state: "hidden", timeout: 3000 }).catch(() => {});
  }
}

/**
 * Login via the UI.
 * Assumes the user already exists and is verified.
 */
export async function loginViaUI(
  page: Page,
  email: string,
  password: string,
): Promise<void> {
  await page.goto("/");

  // If already logged in, dismiss any onboarding and return
  const loggedInContent = page.getByText(/portfolio|my units|my learning programs|dashboard overview/i).first();
  if (await loggedInContent.isVisible({ timeout: 2000 }).catch(() => false)) {
    await dismissOnboarding(page);
    return;
  }

  // Click Sign In on landing page (nav bar button or link)
  const navSignIn = page.getByRole("button", { name: /sign in/i }).first();
  await expect(navSignIn).toBeVisible({ timeout: 5000 });
  await navSignIn.click();

  // Wait for the Login component to settle — it fetches /auth/config on mount
  // and may auto-open a registration modal if hasUsers === false.
  await page.waitForResponse(
    (resp) => resp.url().includes("/auth/config"),
    { timeout: 5000 },
  ).catch(() => {});

  await page.waitForTimeout(500);

  // If a registration modal appeared, dismiss it with Escape
  const modal = page.locator("[role='dialog']");
  if (await modal.isVisible({ timeout: 1000 }).catch(() => false)) {
    await page.keyboard.press("Escape");
    await modal.waitFor({ state: "hidden", timeout: 3000 }).catch(() => {});

    if (await modal.isVisible().catch(() => false)) {
      const closeBtn = modal.getByLabel(/close/i).first();
      if (await closeBtn.isVisible().catch(() => false)) {
        await closeBtn.click();
        await modal.waitFor({ state: "hidden", timeout: 3000 }).catch(() => {});
      }
    }
  }

  // Fill login form — wait for it to be ready
  const emailInput = page.getByPlaceholder("Email address");
  await expect(emailInput).toBeVisible({ timeout: 10000 });
  await emailInput.fill(email);
  await page.getByPlaceholder("Password").fill(password);

  // Click the Sign In submit button
  await page
    .locator("button[type='submit']")
    .filter({ hasText: /sign in/i })
    .click();

  // Wait for navigation to dashboard or admin page
  await expect(page).toHaveURL(/\/(dashboard|admin)/, { timeout: 15000 });

  // Dismiss the welcome onboarding modal if it appears (first login)
  await dismissOnboarding(page);
}

/**
 * Login as the admin user (lands on /admin).
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  await loginViaUI(page, ADMIN_USER.email, ADMIN_USER.password);
}

/**
 * Login as the regular user (lands on /dashboard with units).
 * Most tests should use this — admin has a separate admin-only dashboard.
 * Calls ensureUsers() as a safety net to guarantee the user exists.
 */
export async function loginAsUser(page: Page): Promise<void> {
  await ensureUsers();
  await loginViaUI(page, REGULAR_USER.email, REGULAR_USER.password);
}
