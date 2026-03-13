import { test, expect } from "@playwright/test";
import { loginAsUser } from "../helpers/auth.js";

test.describe("File Import", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
  });

  test("can navigate to import page", async ({ page }) => {
    // Click "Import Package" on dashboard
    await page
      .getByRole("button", { name: /import package/i })
      .click();

    await expect(page).toHaveURL(/\/import/, { timeout: 10000 });
  });

  test("import page shows supported file types", async ({ page }) => {
    await page.goto("/import");

    await expect(
      page.getByText(/pdf|docx|pptx/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can navigate to outline import", async ({ page }) => {
    // Click "From Outline" on dashboard
    await page
      .getByRole("button", { name: /from outline/i })
      .click();

    await expect(page).toHaveURL(/\/import\/outline/, { timeout: 10000 });
    await expect(
      page.getByText(/create from unit outline/i),
    ).toBeVisible();
  });

  test("outline import shows upload area", async ({ page }) => {
    await page.goto("/import/outline");

    // Should see the file drop zone
    await expect(
      page.getByText(/drag and drop|upload|browse/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });
});
