import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Materials & Editor", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);
  });

  test("can open content creator from Week 1", async ({ page }) => {
    const main = page.getByRole("main");

    // Click Week 1 accordion
    await main.locator("button").filter({ hasText: /^Week 1/ }).first().click();

    // Wait for accordion to expand and "Add Material" to appear
    const addMaterialBtn = main
      .getByRole("button", { name: /add material/i })
      .first();
    await expect(addMaterialBtn).toBeVisible({ timeout: 5000 });
    await addMaterialBtn.click();

    // Should navigate to the content creator page
    await expect(page).toHaveURL(/\/content\/new/, { timeout: 10000 });

    // Content creator should show title input and editor
    await expect(page.getByPlaceholder("Enter content title...")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Content Editor")).toBeVisible({ timeout: 5000 });
  });

  test("content creator has unit pre-selected", async ({ page }) => {
    const main = page.getByRole("main");
    await main.locator("button").filter({ hasText: /^Week 1/ }).first().click();

    const addMaterialBtn = main
      .getByRole("button", { name: /add material/i })
      .first();
    await expect(addMaterialBtn).toBeVisible({ timeout: 5000 });
    await addMaterialBtn.click();

    await expect(page).toHaveURL(/\/content\/new/, { timeout: 10000 });

    // The unit select should have a value (pre-selected from query param)
    const unitSelect = page.locator("select#unit");
    await expect(unitSelect).toBeVisible({ timeout: 3000 });
    // Should have "Web Development Fundamentals" selected
    await expect(unitSelect).not.toHaveValue("", { timeout: 3000 });
  });

  test("can type in the rich text editor", async ({ page }) => {
    const main = page.getByRole("main");
    await main.locator("button").filter({ hasText: /^Week 1/ }).first().click();

    const addMaterialBtn = main
      .getByRole("button", { name: /add material/i })
      .first();
    await expect(addMaterialBtn).toBeVisible({ timeout: 5000 });
    await addMaterialBtn.click();

    await expect(page).toHaveURL(/\/content\/new/, { timeout: 10000 });

    // Type in the TipTap rich text editor
    const editor = page
      .locator(".ProseMirror, .tiptap, [contenteditable='true']")
      .first();
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.click();
    await editor.pressSequentially(
      "HTML (HyperText Markup Language) is the standard markup language for creating web pages.",
      { delay: 10 },
    );

    await expect(editor).toContainText("HyperText Markup Language");
  });

  test("can create content and save it to the unit", async ({ page }) => {
    const main = page.getByRole("main");
    await main.locator("button").filter({ hasText: /^Week 1/ }).first().click();

    const addMaterialBtn = main
      .getByRole("button", { name: /add material/i })
      .first();
    await expect(addMaterialBtn).toBeVisible({ timeout: 5000 });
    await addMaterialBtn.click();

    await expect(page).toHaveURL(/\/content\/new/, { timeout: 10000 });

    // Fill in the title
    const titleInput = page.getByPlaceholder("Enter content title...");
    await expect(titleInput).toBeVisible({ timeout: 5000 });
    await titleInput.fill("Introduction to HTML");

    // Type content in the rich text editor
    const editor = page
      .locator(".ProseMirror, .tiptap, [contenteditable='true']")
      .first();
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.click();
    await editor.pressSequentially(
      "HTML is the standard markup language for creating web pages.",
      { delay: 10 },
    );

    await expect(editor).toContainText("HTML is the standard markup language");

    // Save — should navigate back to the unit page
    await page
      .getByRole("button", { name: /^save$/i })
      .click();

    await expect(page).toHaveURL(/\/units\//, { timeout: 15000 });
  });

  test("content creator has pedagogy selector", async ({ page }) => {
    const main = page.getByRole("main");
    await main.locator("button").filter({ hasText: /^Week 1/ }).first().click();

    const addMaterialBtn = main
      .getByRole("button", { name: /add material/i })
      .first();
    await expect(addMaterialBtn).toBeVisible({ timeout: 5000 });
    await addMaterialBtn.click();

    await expect(page).toHaveURL(/\/content\/new/, { timeout: 10000 });

    // Should show teaching philosophy / pedagogy selector
    await expect(
      page.getByText(/teaching philosophy/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });
});
