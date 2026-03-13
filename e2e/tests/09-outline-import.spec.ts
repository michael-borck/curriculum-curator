import { test, expect } from "@playwright/test";
import { loginAsUser } from "../helpers/auth.js";

test.describe("Outline Import", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.goto("/import/outline");
  });

  test("page loads with upload area", async ({ page }) => {
    await expect(
      page.getByText(/create from unit outline/i),
    ).toBeVisible({ timeout: 5000 });

    await expect(
      page.getByText(/drag and drop|browse/i).first(),
    ).toBeVisible();
  });

  test("parser selector shows available parsers", async ({ page }) => {
    // If there are multiple parsers, a selector should appear
    const parserSelect = page.locator("select").first();
    if (await parserSelect.isVisible().catch(() => false)) {
      const options = await parserSelect.locator("option").allTextContents();
      expect(options.length).toBeGreaterThanOrEqual(1);
      // Should have Generic at minimum
      expect(options.some((o) => /generic|ai/i.test(o))).toBeTruthy();
    }
  });

  test("can upload a text file and see parse button", async ({ page }) => {
    // Upload a simple text file via the hidden file input
    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles({
      name: "test-outline.txt",
      mimeType: "text/plain",
      buffer: Buffer.from(
        [
          "COMP1002 Advanced Web Development",
          "Credit Points: 25",
          "Semester: 2",
          "",
          "Description: This unit covers advanced web development topics.",
          "",
          "Learning Outcomes:",
          "1. Design complex web applications",
          "2. Apply modern JavaScript frameworks",
          "",
          "Assessment:",
          "Project 60%",
          "Exam 40%",
          "",
          "Schedule:",
          "Week 1: React Fundamentals",
          "Week 2: State Management",
          "Week 3: API Integration",
        ].join("\n"),
      ),
    });

    // File name should appear
    await expect(
      page.getByText("test-outline.txt"),
    ).toBeVisible({ timeout: 5000 });

    // Parse button should appear
    await expect(
      page.getByRole("button", { name: /parse document/i }),
    ).toBeVisible();
  });

  test("can remove selected file", async ({ page }) => {
    // Upload a file first
    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles({
      name: "test.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("test content"),
    });

    await expect(page.getByText("test.txt")).toBeVisible({ timeout: 5000 });

    // Click remove
    await page.getByText(/remove/i).click();

    // File should be gone, upload area should return
    await expect(
      page.getByText(/drag and drop|browse/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });
});
