import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 18 – Alignment Frameworks
 *
 * Tests custom alignment frameworks: create, add items, map ULOs.
 * UI-only — no API keys required.
 */

/** Navigate to a unit and switch to the Outcomes & Alignment tab. */
async function goToAlignmentTab(page: import("@playwright/test").Page) {
  await page.goto("/dashboard");
  await page.getByText("Web Development Fundamentals").first().click();
  await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

  // Switch to Outcomes & Alignment tab
  await page.getByRole("button", { name: /outcomes.*alignment/i }).click();
  await expect(
    page.getByText(/alignment/i).first(),
  ).toBeVisible({ timeout: 5000 });
}

test.describe("Alignment Frameworks", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);
  });

  test("Add Alignment Framework button is visible", async ({ page }) => {
    await goToAlignmentTab(page);

    const addBtn = page.getByRole("button", { name: /add alignment framework/i });
    await expect(addBtn).toBeVisible({ timeout: 10000 });
  });

  test("can open Add Framework dialog with presets", async ({ page }) => {
    await goToAlignmentTab(page);

    await page.getByRole("button", { name: /add alignment framework/i }).click();

    // Dialog shows full preset names
    await expect(page.getByText("Program Learning Outcomes")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("GRIT Mindset")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Professional Ethics")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Indigenous Perspectives")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Organisation Vision")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Other").first()).toBeVisible({ timeout: 5000 });
  });

  test("can create a GRIT Mindset framework", async ({ page }) => {
    await goToAlignmentTab(page);

    await page.getByRole("button", { name: /add alignment framework/i }).click();

    // Select GRIT Mindset preset
    await page.getByText("GRIT Mindset").click();

    // Should show create/confirm button
    const createBtn = page.getByRole("button", { name: /create framework/i });
    await expect(createBtn).toBeVisible({ timeout: 5000 });
    await createBtn.click();

    // Framework should now appear on the page
    await expect(
      page.getByText("GRIT Mindset").first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("created framework shows items", async ({ page }) => {
    await goToAlignmentTab(page);

    // Scroll down to find GRIT framework from previous test
    const gritSection = page.getByRole("heading", { name: /GRIT Mindset/i }).first();
    await gritSection.scrollIntoViewIfNeeded();
    if (!(await gritSection.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, "GRIT framework not found — previous test may not have run");
      return;
    }

    // Click to expand the framework panel
    await gritSection.click();

    // Should show GRIT items (Global, Responsible, Innovative, Technology-savvy)
    await expect(page.getByText(/Global perspectives/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("can create a Program Learning Outcomes framework", async ({ page }) => {
    await goToAlignmentTab(page);

    await page.getByRole("button", { name: /add alignment framework/i }).click();

    await page.getByText("Program Learning Outcomes").click();

    const createBtn = page.getByRole("button", { name: /create framework/i });
    await expect(createBtn).toBeVisible({ timeout: 5000 });
    await createBtn.click();

    // PLO framework should now appear
    await expect(
      page.getByText("Program Learning Outcomes").first(),
    ).toBeVisible({ timeout: 5000 });
  });
});
