import { test, expect } from "@playwright/test";
import { loginAsUser } from "../helpers/auth.js";

test.describe("Create Unit", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
  });

  test("create a unit via New Learning Program button", async ({ page }) => {
    // Click "New Learning Program"
    await page.getByRole("button", { name: "New Learning Program", exact: true }).click();

    // Modal should appear
    await expect(page.getByText(/create new (unit|learning program)/i)).toBeVisible({ timeout: 5000 });

    // Fill in unit details
    await page.getByPlaceholder(/programming fundamentals/i).fill("Web Development Fundamentals");
    await page.getByPlaceholder(/e\.g\.,? (CS101|ICTPRG302|LP-001)/i).fill("ICT101");
    await page
      .getByPlaceholder("Brief description of the unit...")
      .fill("An introductory unit covering HTML, CSS, and JavaScript.");

    // Semester structure should be default — click it to ensure
    await page.getByRole("button", { name: /^semester$/i }).click();

    // Scroll down and submit
    await page
      .getByRole("button", { name: /create learning program|create unit/i })
      .click();

    // Should navigate to the new unit page
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });

    // Unit title should be visible on the page
    await expect(
      page.getByText("Web Development Fundamentals").first(),
    ).toBeVisible();
  });

  test("unit appears on the dashboard", async ({ page }) => {
    // Should see the unit card on dashboard
    await expect(
      page.getByRole("main").getByText("Web Development Fundamentals").first(),
    ).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("ICT101").first()).toBeVisible();
  });

  test("can navigate into the unit", async ({ page }) => {
    // Click on the unit card
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();

    // Should land on unit page with tabs
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await expect(
      page.getByRole("main").getByText("Structure & Content"),
    ).toBeVisible();
  });

  test("create a second unit with different preset", async ({ page }) => {
    await page.getByRole("button", { name: "New Learning Program", exact: true }).click();
    await expect(page.getByText(/create new (unit|learning program)/i)).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/programming fundamentals/i).fill("Data Science Essentials");
    await page.getByPlaceholder(/e\.g\.,? (CS101|ICTPRG302|LP-001)/i).fill("DSC201");

    // Select "Trimester" preset
    await page.getByRole("button", { name: /^trimester$/i }).click();

    await page
      .getByRole("button", { name: /create learning program|create unit/i })
      .click();

    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await expect(page.getByText("Data Science Essentials").first()).toBeVisible();
  });
});
