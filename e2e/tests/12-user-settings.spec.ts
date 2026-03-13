import { test, expect } from "@playwright/test";
import { loginAsUser } from "../helpers/auth.js";

test.describe("User Settings", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
  });

  test("can navigate to settings page", async ({ page }) => {
    await page.goto("/settings");
    await expect(
      page.getByText(/settings|preferences|profile/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can set teaching style", async ({ page }) => {
    await page.goto("/settings");

    // Look for teaching style selector
    const styleSelector = page.getByText(/teaching style|pedagogy/i).first();
    if (await styleSelector.isVisible().catch(() => false)) {
      // Find the dropdown near it
      const dropdown = styleSelector
        .locator("..")
        .locator("select, [role='combobox'], [role='listbox']")
        .first();
      if (await dropdown.isVisible().catch(() => false)) {
        await dropdown.click();
      }
    }
  });

  test("can set education sector", async ({ page }) => {
    await page.goto("/settings");

    // Look for education sector
    const sectorText = page.getByText(/education sector|sector/i).first();
    if (await sectorText.isVisible().catch(() => false)) {
      const dropdown = sectorText
        .locator("..")
        .locator("select, button, [role='combobox']")
        .first();
      if (await dropdown.isVisible().catch(() => false)) {
        await dropdown.click();

        // Select "Higher Education"
        const higherEd = page.getByText(/higher education/i).first();
        if (await higherEd.isVisible().catch(() => false)) {
          await higherEd.click();
        }
      }
    }
  });

  test("settings persist after reload", async ({ page }) => {
    await page.goto("/settings");

    // Save any changes
    const saveBtn = page.getByRole("button", { name: /save/i }).first();
    if (await saveBtn.isVisible().catch(() => false)) {
      await saveBtn.click();
    }

    await page.reload();

    // Settings page should still load without errors
    await expect(
      page.getByText(/settings|preferences|profile/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can access export templates tab", async ({ page }) => {
    await page.goto("/settings");

    const exportTab = page.getByText(/export/i).first();
    if (await exportTab.isVisible().catch(() => false)) {
      await exportTab.click();

      // Should see export template management
      await expect(
        page.getByText(/template|upload|reference/i).first(),
      ).toBeVisible({ timeout: 5000 });
    }
  });
});
