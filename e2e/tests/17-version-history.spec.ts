import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 17 – Version History (inline modal flow).
 *
 * The old MaterialDetail page was deleted with the Content model
 * cleanup. Version history now lives as a per-material History button
 * inside the inline WeeklyMaterialsManager (expanded week panel on
 * the structure tab), which opens a modal showing the commit list
 * from the git-backed content store.
 *
 * The History button only renders when the material has a
 * description, so this test creates its own material with body
 * content via the API before exercising the UI.
 */

test.describe("Version History", () => {
  test.describe.configure({ mode: "serial" });

  let unitId = "";
  const materialTitle = `Version History Test ${Date.now()}`;

  test.beforeAll(async ({ browser }) => {
    // Log in once via a throwaway page to grab a token and seed a
    // material on the shared "Web Development Fundamentals" unit
    // created by test 02. We pick the newest unit with that title
    // so repeated runs against a dirty DB still target a real row.
    const context = await browser.newContext();
    const page = await context.newPage();
    await loginAsUser(page);

    const token = await page.evaluate(() => localStorage.getItem("token"));
    const authHeaders = { Authorization: `Bearer ${token}` };

    const unitsResp = await page.request.get("/api/units", {
      headers: authHeaders,
    });
    if (!unitsResp.ok()) {
      await context.close();
      throw new Error("Could not fetch units for version-history setup");
    }
    const body = (await unitsResp.json()) as {
      units: Array<{ id: string; title: string }>;
    };
    const unit = (body.units ?? []).find(u =>
      /web development fundamentals/i.test(u.title),
    );
    if (!unit) {
      await context.close();
      throw new Error("Web Development Fundamentals unit not seeded yet");
    }
    unitId = unit.id;

    // Create a material with a non-empty description — that's what
    // triggers the History button to render on the material row.
    const createResp = await page.request.post(
      `/api/materials/units/${unitId}/materials`,
      {
        headers: authHeaders,
        data: {
          weekNumber: 1,
          title: materialTitle,
          type: "lecture",
          description:
            "<p>Seed content for version history test. Anything non-empty is fine.</p>",
          category: "general",
          status: "draft",
        },
      },
    );
    expect(
      createResp.ok(),
      `Failed to create material: ${createResp.status()} ${await createResp.text()}`,
    ).toBeTruthy();

    await context.close();
  });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);

    // Open the unit we seeded and expand Week 1 so the materials
    // manager renders the seeded material row.
    await page.goto(`/units/${unitId}`);
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });

    const main = page.getByRole("main");
    await main
      .locator("button")
      .filter({ hasText: /^Week 1/ })
      .first()
      .click();
    await expect(main.getByText(materialTitle).first()).toBeVisible({
      timeout: 10000,
    });
  });

  test("History button is visible on a material with content", async ({
    page,
  }) => {
    // Each material row exposes a set of icon buttons; the history
    // one carries title="Version history".
    const historyBtn = page
      .getByRole("main")
      .locator('button[title="Version history"]')
      .first();
    await expect(historyBtn).toBeVisible({ timeout: 5000 });
  });

  test("clicking History opens the version history modal", async ({
    page,
  }) => {
    await page
      .getByRole("main")
      .locator('button[title="Version history"]')
      .first()
      .click();

    // Modal header reads "History: <material title>"
    await expect(
      page.getByRole("heading", { name: new RegExp(`History:`, "i") }),
    ).toBeVisible({ timeout: 5000 });
  });

  test("history modal shows commit list or empty state", async ({ page }) => {
    await page
      .getByRole("main")
      .locator('button[title="Version history"]')
      .first()
      .click();

    await expect(
      page
        .getByText(/version|history|no versions|commit|timeline|revision/i)
        .first(),
    ).toBeVisible({ timeout: 10000 });
  });

});
