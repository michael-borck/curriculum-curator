import { test, expect } from "@playwright/test";
import { ADMIN_USER, REGULAR_USER, API_BASE } from "../helpers/constants.js";
import { autoVerifyUser, userExists } from "../helpers/db.js";

test.describe("Registration & Login", () => {
  test.describe.configure({ mode: "serial" });

  test("register first user as admin (auto-verified)", async ({ page }) => {
    await page.goto("/");

    // Click Sign In on landing page — auto-detects no users, shows registration
    await page.getByRole("button", { name: /sign in/i }).first().click();

    // The registration modal should appear (first-user setup)
    await expect(
      page.getByRole("heading", { name: /set up your admin account/i }),
    ).toBeVisible({ timeout: 10000 });

    // Fill registration form
    await page.getByPlaceholder("John Doe").fill(ADMIN_USER.name);
    await page.getByPlaceholder("john@example.com").fill(ADMIN_USER.email);
    await page.getByPlaceholder("••••••••").first().fill(ADMIN_USER.password);
    await page.getByPlaceholder("••••••••").nth(1).fill(ADMIN_USER.password);

    // Submit
    await page.getByRole("button", { name: /create account/i }).click();

    // First user is auto-verified — should see "Welcome, Administrator!" success
    await expect(
      page.getByText("Welcome, Administrator!"),
    ).toBeVisible({ timeout: 10000 });
  });

  test("register regular user via API and verify via DB", async () => {
    // Register via API (second user, not auto-verified)
    const resp = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: REGULAR_USER.name,
        email: REGULAR_USER.email,
        password: REGULAR_USER.password,
      }),
    });
    expect(resp.ok, `Registration API returned ${resp.status}`).toBe(true);

    // Verify user exists in DB
    expect(userExists(REGULAR_USER.email)).toBe(true);

    // Auto-verify via direct DB update (skip email flow)
    const verified = autoVerifyUser(REGULAR_USER.email);
    expect(verified, "autoVerifyUser should update the user").toBe(true);
  });

  test("regular user can login", async ({ page }) => {
    await page.goto("/");

    await page
      .getByRole("navigation")
      .getByRole("button", { name: /sign in/i })
      .click();

    // Wait for Login component to settle
    await page.waitForResponse(
      (resp) => resp.url().includes("/auth/config"),
      { timeout: 5000 },
    ).catch(() => {});
    await page.waitForTimeout(500);

    // Dismiss registration modal if it appeared
    const modal = page.locator("[role='dialog']");
    if (await modal.isVisible({ timeout: 1000 }).catch(() => false)) {
      await page.keyboard.press("Escape");
      await modal.waitFor({ state: "hidden", timeout: 3000 }).catch(() => {});
    }

    await page.getByPlaceholder("Email address").fill(REGULAR_USER.email);
    await page.getByPlaceholder("Password").fill(REGULAR_USER.password);
    await page
      .locator("button[type='submit']")
      .filter({ hasText: /sign in/i })
      .click();

    // Regular user should reach the dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Dashboard should show content
    await expect(
      page.getByText(/portfolio|my units/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("login with wrong password shows error", async ({ page }) => {
    await page.goto("/");

    await page
      .getByRole("navigation")
      .getByRole("button", { name: /sign in/i })
      .click();

    // Wait for Login component to settle
    await page.waitForResponse(
      (resp) => resp.url().includes("/auth/config"),
      { timeout: 5000 },
    ).catch(() => {});
    await page.waitForTimeout(500);

    // Dismiss registration modal if it appeared
    const modal = page.locator("[role='dialog']");
    if (await modal.isVisible({ timeout: 1000 }).catch(() => false)) {
      await page.keyboard.press("Escape");
      await modal.waitFor({ state: "hidden", timeout: 3000 }).catch(() => {});
    }

    await page.getByPlaceholder("Email address").fill(REGULAR_USER.email);
    await page.getByPlaceholder("Password").fill("WrongPassword123!");
    await page
      .locator("button[type='submit']")
      .filter({ hasText: /sign in/i })
      .click();

    await expect(
      page.getByText(/invalid|incorrect|failed/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });
});
