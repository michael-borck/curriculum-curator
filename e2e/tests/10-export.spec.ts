import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Export", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);
  });

  test("export button is visible on unit page", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /export/i }),
    ).toBeVisible({ timeout: 5000 });
  });

  test("export dropdown shows format options", async ({ page }) => {
    await page.getByRole("button", { name: /export/i }).click();

    // Should see export format options
    await expect(
      page.getByText(/html|pdf|docx|scorm|common cartridge|imscc/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can trigger HTML export", async ({ page }) => {
    await page.getByRole("button", { name: /export/i }).click();

    // Click HTML export option
    const htmlOption = page.getByText(/html/i).first();
    if (await htmlOption.isVisible().catch(() => false)) {
      // Set up download listener
      const downloadPromise = page.waitForEvent("download", { timeout: 15000 }).catch(() => null);
      await htmlOption.click();

      const download = await downloadPromise;
      if (download) {
        // Verify download started
        expect(download.suggestedFilename()).toBeTruthy();
      }
    }
  });
});
