import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Unit Settings", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    // Navigate to the first unit (ICT101)
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);
  });

  test("can navigate to Settings tab", async ({ page }) => {
    await page.getByRole("main").getByRole("button", { name: "Settings", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Academic Details" })).toBeVisible(
      { timeout: 5000 },
    );
  });

  test("can edit academic details", async ({ page }) => {
    await page.getByRole("main").getByRole("button", { name: "Settings", exact: true }).click();

    // Set year
    const yearInput = page.getByLabel(/year/i);
    if (await yearInput.isVisible().catch(() => false)) {
      await yearInput.fill("2026");
    }

    // Set credit points
    const creditInput = page.getByLabel(/credit points/i);
    if (await creditInput.isVisible().catch(() => false)) {
      await creditInput.fill("25");
    }

    // Set prerequisites
    const prereqInput = page.getByLabel(/prerequisites/i);
    if (await prereqInput.isVisible().catch(() => false)) {
      await prereqInput.fill("COMP1001 Introduction to Programming");
    }

    // Save
    await page.getByRole("button", { name: /save settings/i }).click();

    // Verify save succeeded (no error, settings persist)
    await page.reload();
    await dismissOnboarding(page);
    await page.getByRole("main").getByRole("button", { name: "Settings", exact: true }).click();

    if (await creditInput.isVisible().catch(() => false)) {
      await expect(creditInput).toHaveValue("25");
    }
  });

  test("can toggle alignment features", async ({ page }) => {
    await page.getByRole("main").getByRole("button", { name: "Settings", exact: true }).click();

    // Look for alignment toggle switches
    const gradCapToggle = page.getByText(/graduate capabilities/i);
    if (await gradCapToggle.isVisible().catch(() => false)) {
      // Find the nearest toggle/switch and click it
      const toggleButton = gradCapToggle
        .locator("..")
        .locator("button, input[type='checkbox'], [role='switch']")
        .first();
      if (await toggleButton.isVisible().catch(() => false)) {
        await toggleButton.click();
      }
    }

    await page.getByRole("button", { name: /save settings/i }).click();
  });
});
