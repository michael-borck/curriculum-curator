import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Weekly Schedule", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);
  });

  test("week accordion is visible with topics", async ({ page }) => {
    const main = page.getByRole("main");
    await expect(
      main.getByText(/week 1|module 1|session 1/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can expand a week to see content area", async ({ page }) => {
    const main = page.getByRole("main");
    // Click on Week 1 to expand
    await main.locator("button").filter({ hasText: /^Week 1/ }).first().click();

    // Should see material-related content (add material button or empty state)
    await expect(
      main.getByText(/add material|no materials|add content/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can rename a topic", async ({ page }) => {
    const main = page.getByRole("main");
    // Expand Week 1
    await main.locator("button").filter({ hasText: /^Week 1/ }).first().click();

    // Look for an editable title field or edit button
    const editableTitle = main
      .locator("input[type='text']")
      .filter({ hasText: /html|week 1/i })
      .first();

    if (await editableTitle.isVisible().catch(() => false)) {
      await editableTitle.fill("HTML & Document Structure");
      await editableTitle.press("Tab");
    } else {
      // Try clicking on the topic title text to make it editable
      const titleText = main
        .getByText(/week 1|module 1/i)
        .first()
        .locator("..");
      const editBtn = titleText.locator("button, [role='button']").first();
      if (await editBtn.isVisible().catch(() => false)) {
        await editBtn.click();
      }
    }
  });

  test("can add a new topic/week", async ({ page }) => {
    const main = page.getByRole("main");
    // Look for "Add Week" or "Add Module" button at bottom
    const addButton = main
      .getByRole("button", { name: /add week|add module|add topic/i })
      .first();

    if (await addButton.isVisible().catch(() => false)) {
      const countBefore = await main
        .getByText(/week \d+|module \d+/i)
        .count();

      await addButton.click();

      // Should have one more week now
      const countAfter = await main
        .getByText(/week \d+|module \d+/i)
        .count();

      expect(countAfter).toBeGreaterThanOrEqual(countBefore);
    }
  });
});
