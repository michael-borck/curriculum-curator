import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

test.describe("Quality & Analytics", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.getByRole("main").getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    await dismissOnboarding(page);
  });

  test("analytics tab shows unit overview", async ({ page }) => {
    await page.getByRole("main").getByRole("button", { name: /analytics/i }).click();

    // Should see some analytics content
    await expect(
      page.getByText(/overview|progress|bloom|workload|structure/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("quality tab shows quality dashboard", async ({ page }) => {
    await page.getByRole("main").getByRole("button", { name: /quality/i }).click();

    // Should see quality-related content
    await expect(
      page.getByText(/quality|score|dashboard|udl/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("quality dashboard shows scoring dimensions", async ({ page }) => {
    await page.getByRole("main").getByRole("button", { name: /quality/i }).click();

    // Look for quality dimension names
    const dimensions = [
      /completeness/i,
      /content quality/i,
      /alignment/i,
      /workload/i,
      /diversity/i,
      /assessment/i,
    ];

    let found = 0;
    for (const dim of dimensions) {
      if (
        await page
          .getByText(dim)
          .first()
          .isVisible()
          .catch(() => false)
      ) {
        found++;
      }
    }

    // Should find at least some quality dimensions
    expect(found).toBeGreaterThanOrEqual(1);
  });

  test("UDL dashboard is accessible", async ({ page }) => {
    await page.getByRole("main").getByRole("button", { name: /quality/i }).click();

    // Look for UDL section
    const udlText = page.getByText(/udl|universal design/i).first();
    if (await udlText.isVisible().catch(() => false)) {
      // Should show UDL sub-scores
      const udlDimensions = [
        /representation/i,
        /engagement/i,
        /expression/i,
        /accessibility/i,
      ];

      let found = 0;
      for (const dim of udlDimensions) {
        if (
          await page
            .getByText(dim)
            .first()
            .isVisible()
            .catch(() => false)
        ) {
          found++;
        }
      }

      expect(found).toBeGreaterThanOrEqual(1);
    }
  });
});
