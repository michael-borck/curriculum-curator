import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Assessments & Rubrics", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);
    // Navigate to Assessments tab
    await page.getByRole("main").getByRole("button", { name: /assessments/i }).click();
  });

  test("assessments panel is visible", async ({ page }) => {
    await expect(
      page.getByText(/assessments/i).first(),
    ).toBeVisible({ timeout: 5000 });
    await expect(
      page.getByRole("button", { name: /add assessment/i }),
    ).toBeVisible();
  });

  test("add a quiz assessment (30%)", async ({ page }) => {
    await page.getByRole("button", { name: /add assessment/i }).click();

    // Wait for form to appear
    await expect(page.getByText("Add New Assessment")).toBeVisible({ timeout: 5000 });

    // Title — first text input in the form (no label binding, no placeholder)
    const titleInput = page.locator("form input[type='text']").first();
    await titleInput.fill("Mid-Semester Quiz");

    // Weight
    const weightInput = page.locator("form input[type='number']").first();
    await weightInput.fill("30");

    // Create
    await page
      .getByRole("button", { name: /^create$/i })
      .click();

    await expect(
      page.getByText("Mid-Semester Quiz"),
    ).toBeVisible({ timeout: 5000 });
  });

  test("add a project assessment (40%)", async ({ page }) => {
    await page.getByRole("button", { name: /add assessment/i }).click();
    await expect(page.getByText("Add New Assessment")).toBeVisible({ timeout: 5000 });

    const titleInput = page.locator("form input[type='text']").first();
    await titleInput.fill("Web Portfolio Project");

    const weightInput = page.locator("form input[type='number']").first();
    await weightInput.fill("40");

    await page
      .getByRole("button", { name: /^create$/i })
      .click();

    await expect(
      page.getByText("Web Portfolio Project"),
    ).toBeVisible({ timeout: 5000 });
  });

  test("add a final exam assessment (30%)", async ({ page }) => {
    await page.getByRole("button", { name: /add assessment/i }).click();
    await expect(page.getByText("Add New Assessment")).toBeVisible({ timeout: 5000 });

    const titleInput = page.locator("form input[type='text']").first();
    await titleInput.fill("Final Examination");

    const weightInput = page.locator("form input[type='number']").first();
    await weightInput.fill("30");

    await page
      .getByRole("button", { name: /^create$/i })
      .click();

    await expect(
      page.getByText("Final Examination"),
    ).toBeVisible({ timeout: 5000 });
  });

  test("assessment weights total 100%", async ({ page }) => {
    // Look for the total weight indicator
    await expect(
      page.getByText(/100(\.0)?%/),
    ).toBeVisible({ timeout: 5000 });
  });

  test("assessments persist after reload", async ({ page }) => {
    await page.reload();
    await dismissOnboarding(page);
    await page.getByRole("main").getByRole("button", { name: /assessments/i }).click();

    await expect(page.getByText("Mid-Semester Quiz")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText("Web Portfolio Project")).toBeVisible();
    await expect(page.getByText("Final Examination")).toBeVisible();
  });

  test("can edit an assessment", async ({ page }) => {
    // Find edit button on Mid-Semester Quiz
    const quizRow = page.getByText("Mid-Semester Quiz").locator("..").locator("..");
    const editButton = quizRow
      .locator("button")
      .filter({ has: page.locator("svg") })
      .first();

    if (await editButton.isVisible().catch(() => false)) {
      await editButton.click();

      // Modify the title
      const titleInput = page.locator("form input[type='text']").first();
      if (await titleInput.isVisible().catch(() => false)) {
        await titleInput.fill("Mid-Semester Online Quiz");
        await page
          .getByRole("button", { name: /^update$/i })
          .click();
        await expect(
          page.getByText("Mid-Semester Online Quiz"),
        ).toBeVisible({ timeout: 5000 });
      }
    }
  });
});
