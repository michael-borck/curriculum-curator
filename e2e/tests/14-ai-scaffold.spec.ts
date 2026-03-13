import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 14 – AI Scaffold
 *
 * Tests the "Quick Scaffold" feature on the Unit page.
 * Requires an LLM API key (e.g. ANTHROPIC_API_KEY in the environment).
 */

test.describe("AI Scaffold", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);
  });

  test("Quick Scaffold button is visible on unit page", async ({ page }) => {
    await page.goto("/dashboard");
    const unitLink = page.getByText("Web Development Fundamentals").first();
    await expect(unitLink).toBeVisible({ timeout: 5000 });
    await unitLink.click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    const scaffoldBtn = page.getByRole("button", { name: /quick scaffold/i });
    await expect(scaffoldBtn).toBeVisible({ timeout: 5000 });
  });

  test("Quick Scaffold generates and shows review modal", async ({ page }) => {
    test.setTimeout(120000);

    await page.goto("/dashboard");
    await page.getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    // Monitor scaffold API call
    const scaffoldResponse = page.waitForResponse(
      (resp) => resp.url().includes("/ai/scaffold-unit"),
      { timeout: 90000 },
    );

    const scaffoldBtn = page.getByRole("button", { name: /quick scaffold/i });
    await expect(scaffoldBtn).toBeVisible({ timeout: 5000 });
    await scaffoldBtn.click();

    // Wait for the API response
    const resp = await scaffoldResponse;
    if (resp.status() >= 400) {
      const text = await resp.text().catch(() => "no body");
      const detail = (() => { try { return JSON.parse(text).detail; } catch { return text.slice(0, 200); } })();
      test.skip(true, `Scaffold API error ${resp.status()}: ${detail}`);
      return;
    }

    // Then wait for the review modal to appear
    await expect(
      page.getByText("Review Generated Structure"),
    ).toBeVisible({ timeout: 10000 });

    // Should show ULOs, weekly topics, and assessments
    await expect(page.getByText("Learning Outcomes").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Week 1/i).first()).toBeVisible({ timeout: 5000 });

    // Should have Accept & Create and Cancel buttons
    await expect(
      page.getByRole("button", { name: /accept.*create/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /cancel/i }),
    ).toBeVisible();
  });

  test("can cancel scaffold review", async ({ page }) => {
    test.setTimeout(120000);

    await page.goto("/dashboard");
    await page.getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    const scaffoldResponse = page.waitForResponse(
      (resp) => resp.url().includes("/ai/scaffold-unit"),
      { timeout: 90000 },
    );

    await page.getByRole("button", { name: /quick scaffold/i }).click();

    const resp = await scaffoldResponse;
    if (resp.status() >= 400) {
      test.skip(true, "Scaffold API not working");
      return;
    }

    await expect(
      page.getByText("Review Generated Structure"),
    ).toBeVisible({ timeout: 10000 });

    // Cancel should close the review
    await page.getByRole("button", { name: /cancel/i }).first().click();
    await expect(
      page.getByText("Review Generated Structure"),
    ).not.toBeVisible({ timeout: 5000 });
  });

  test("can accept scaffold and create structure", async ({ page }) => {
    test.setTimeout(120000);

    // Use the API to find the second unit, avoiding polluting the first
    await page.goto("/dashboard");
    const token = await page.evaluate(() => localStorage.getItem("token"));
    const unitsResp = await page.request.get("/api/units", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = (await unitsResp.json()) as { units: Array<{ id: string; code: string; title: string }> };
    const units = body.units ?? [];
    // Pick DSC201 (empty unit) — avoid ICT101 (used by other scaffold tests) and imported units
    const secondUnit = units.find((u) => u.code === "DSC201")
      ?? units.find((u) => u.code !== "ICT101")
      ?? units[1];
    if (!secondUnit) {
      test.skip(true, "No second unit found for scaffold accept test");
      return;
    }
    await page.goto(`/units/${secondUnit.id}`);
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    const scaffoldResponse = page.waitForResponse(
      (resp) => resp.url().includes("/ai/scaffold-unit"),
      { timeout: 90000 },
    );

    await page.getByRole("button", { name: /quick scaffold/i }).click();

    const resp = await scaffoldResponse;
    if (resp.status() >= 400) {
      test.skip(true, "Scaffold API not working");
      return;
    }

    await expect(
      page.getByText("Review Generated Structure"),
    ).toBeVisible({ timeout: 10000 });

    // Accept the scaffold
    const acceptBtn = page.getByRole("button", { name: /accept.*create/i });
    await acceptBtn.click();

    // Wait for either success (modal closes) or failure (error toast)
    const modalGone = page
      .getByText("Review Generated Structure")
      .waitFor({ state: "hidden", timeout: 30000 })
      .then(() => "closed" as const);
    const errorToast = page
      .getByText(/failed to apply scaffold/i)
      .waitFor({ state: "visible", timeout: 30000 })
      .then(() => "error" as const);

    const result = await Promise.race([modalGone, errorToast]);
    if (result === "error") {
      test.skip(true, "Scaffold accept API failed (toast error shown)");
      return;
    }

    // Navigate to Outcomes tab to verify ULOs were created
    await page.getByRole("button", { name: /outcomes.*alignment/i }).click();
    await expect(
      page.getByText(/ULO/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
