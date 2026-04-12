import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Materials & Editor", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page
      .getByRole("main")
      .getByText("Web Development Fundamentals")
      .first()
      .click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);

    // Expand Week 1 — reveals the inline WeeklyMaterialsManager
    const main = page.getByRole("main");
    await main
      .locator("button")
      .filter({ hasText: /^Week 1/ })
      .first()
      .click();
  });

  test("expanded week shows the inline materials manager", async ({ page }) => {
    const main = page.getByRole("main");
    // The manager renders an "Add Material" button in-place (no page navigation)
    await expect(
      main.getByRole("button", { name: /add material/i }).first(),
    ).toBeVisible({ timeout: 5000 });
    // URL should still be the unit page — no navigation away
    await expect(page).toHaveURL(/\/units\/[^/]+$/);
  });

  test("can open the inline create form from Add Material", async ({ page }) => {
    const main = page.getByRole("main");
    await main
      .getByRole("button", { name: /add material/i })
      .first()
      .click();

    // Inline form appears with a title field and session format combobox
    await expect(
      main.getByPlaceholder(/introduction to/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can type in the inline form title field", async ({ page }) => {
    const main = page.getByRole("main");
    await main
      .getByRole("button", { name: /add material/i })
      .first()
      .click();

    const titleInput = main
      .getByPlaceholder(/introduction to/i)
      .first();
    await expect(titleInput).toBeVisible({ timeout: 5000 });
    await titleInput.fill("Introduction to HTML");
    await expect(titleInput).toHaveValue("Introduction to HTML");
  });

  test("can create a material and see it in the week list", async ({ page }) => {
    const main = page.getByRole("main");
    await main
      .getByRole("button", { name: /add material/i })
      .first()
      .click();

    const titleInput = main
      .getByPlaceholder(/introduction to/i)
      .first();
    await expect(titleInput).toBeVisible({ timeout: 5000 });
    await titleInput.fill("E2E Test Material");

    // Submit the form — the manager has a Create button
    await main
      .getByRole("button", { name: /^create$|^save$/i })
      .first()
      .click();

    // New material row appears in the expanded week
    await expect(
      main.getByText("E2E Test Material").first(),
    ).toBeVisible({ timeout: 10000 });

    // Still on the unit page — no route change
    await expect(page).toHaveURL(/\/units\/[^/]+$/);
  });
});
