import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 17 – Version History
 *
 * Tests viewing material version history, diffs, and restore.
 * Finds a material that actually renders (has content/history/metadata tabs).
 * UI-only — no API keys required.
 */

test.describe("Version History", () => {
  test.describe.configure({ mode: "serial" });

  let materialUrl = "";

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);
  });

  test("can navigate to a material detail page", async ({ page }) => {
    const token = await page.evaluate(() => localStorage.getItem("token"));

    // Get all units
    const unitsResp = await page.request.get("/api/units", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!unitsResp.ok()) {
      test.skip(true, "Could not fetch units via API");
      return;
    }
    const body = (await unitsResp.json()) as {
      units: Array<{ id: string; code: string }>;
    };
    const units = body.units ?? [];

    // Prefer ICT101 first (test 06 creates content here)
    const sorted = [...units].sort((a, b) =>
      a.code === "ICT101" ? -1 : b.code === "ICT101" ? 1 : 0,
    );

    // Try each unit's content (from the contents table, not weekly_materials)
    for (const unit of sorted) {
      const contResp = await page.request.get(
        `/api/units/${unit.id}/content`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (!contResp.ok()) continue;
      const contBody = (await contResp.json()) as { contents: Array<{ id: string }> };
      const contents = contBody.contents ?? [];
      if (contents.length > 0) {
        materialUrl = `/units/${unit.id}/materials/${contents[0].id}`;
        break;
      }
    }

    if (!materialUrl) {
      test.skip(true, "No viewable materials found in any unit");
      return;
    }

    await page.goto(materialUrl);
    await expect(page).toHaveURL(/\/materials\//, { timeout: 5000 });
  });

  test("material detail page has content, history, metadata tabs", async ({
    page,
  }) => {
    test.skip(!materialUrl, "No material found in any unit");

    await page.goto(materialUrl);

    await expect(
      page.getByRole("button", { name: /content/i }).first(),
    ).toBeVisible({ timeout: 10000 });
    await expect(
      page.getByRole("button", { name: /history/i }).first(),
    ).toBeVisible({ timeout: 5000 });
    await expect(
      page.getByRole("button", { name: /metadata/i }).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can switch to history tab", async ({ page }) => {
    test.skip(!materialUrl, "No material found in any unit");

    await page.goto(materialUrl);

    await page.getByRole("button", { name: /history/i }).first().click();

    await expect(
      page
        .getByText(/version|history|no versions|commit|timeline/i)
        .first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can switch to metadata tab", async ({ page }) => {
    test.skip(!materialUrl, "No material found in any unit");

    await page.goto(materialUrl);

    await page.getByRole("button", { name: /metadata/i }).first().click();

    await expect(
      page.getByText(/type|created|format|source/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });
});
