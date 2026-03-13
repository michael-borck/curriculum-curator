import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Learning Outcomes (ULOs)", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);
    // Navigate to Outcomes & Alignment tab
    await page.getByRole("main").getByRole("button", { name: /outcomes/i }).click();
  });

  test("ULO manager is visible", async ({ page }) => {
    await expect(
      page.getByText(/unit learning outcomes/i),
    ).toBeVisible({ timeout: 5000 });
    await expect(
      page.getByRole("button", { name: /add ulo/i }),
    ).toBeVisible();
  });

  test("add first ULO manually", async ({ page }) => {
    await page.getByRole("button", { name: /add ulo/i }).click();

    // Fill ULO form
    await page.getByPlaceholder(/code/i).fill("ULO1");
    await page
      .getByPlaceholder(/description/i)
      .fill(
        "Construct responsive web pages using HTML5 and CSS3",
      );

    // Select Bloom's level — find the dropdown for bloom
    const bloomSelect = page.locator("select").filter({ hasText: /apply/i });
    if (await bloomSelect.isVisible().catch(() => false)) {
      await bloomSelect.selectOption("Apply");
    } else {
      // Try alternative — a dropdown that has bloom levels
      const anySelect = page
        .locator("select")
        .filter({ hasText: /remember|understand/i })
        .first();
      if (await anySelect.isVisible().catch(() => false)) {
        await anySelect.selectOption("apply");
      }
    }

    // Save
    await page.getByRole("button", { name: /save/i }).first().click();

    // Verify ULO appears in list
    await expect(page.getByText("ULO1")).toBeVisible({ timeout: 5000 });
    await expect(
      page.getByText(/construct responsive web pages/i),
    ).toBeVisible();
  });

  test("add second ULO", async ({ page }) => {
    await page.getByRole("button", { name: /add ulo/i }).click();

    await page.getByPlaceholder(/code/i).fill("ULO2");
    await page
      .getByPlaceholder(/description/i)
      .fill("Analyse web application architectures and design patterns");

    // Select Analyse level
    const bloomSelect = page
      .locator("select")
      .filter({ hasText: /understand|apply|remember/i })
      .first();
    if (await bloomSelect.isVisible().catch(() => false)) {
      await bloomSelect.selectOption("analyze");
    }

    await page.getByRole("button", { name: /save/i }).first().click();

    await expect(page.getByText("ULO2")).toBeVisible({ timeout: 5000 });
  });

  test("add third ULO", async ({ page }) => {
    await page.getByRole("button", { name: /add ulo/i }).click();

    await page.getByPlaceholder(/code/i).fill("ULO3");
    await page
      .getByPlaceholder(/description/i)
      .fill("Design and implement a complete web application");

    await page.getByRole("button", { name: /save/i }).first().click();

    await expect(page.getByText("ULO3")).toBeVisible({ timeout: 5000 });
  });

  test("ULOs persist after page reload", async ({ page }) => {
    await page.reload();
    await dismissOnboarding(page);
    await page.getByRole("main").getByRole("button", { name: /outcomes/i }).click();

    await expect(page.getByText("ULO1")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("ULO2")).toBeVisible();
    await expect(page.getByText("ULO3")).toBeVisible();
  });

  test("can edit a ULO", async ({ page }) => {
    // Click edit on ULO1
    const ulo1Row = page.getByText("ULO1").locator("..").locator("..");
    const editButton = ulo1Row.getByRole("button").filter({ has: page.locator("svg") }).first();
    await editButton.click();

    // Modify description
    const descInput = page.locator("input[value*='onstruct responsive'], textarea").first();
    if (await descInput.isVisible().catch(() => false)) {
      await descInput.fill(
        "Build responsive web pages using modern HTML5 and CSS3 techniques",
      );
      await page.getByRole("button", { name: /save/i }).first().click();
      await expect(
        page.getByText(/build responsive web pages/i),
      ).toBeVisible({ timeout: 5000 });
    }
  });
});
