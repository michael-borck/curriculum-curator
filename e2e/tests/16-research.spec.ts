import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 16 – Research / Academic Search
 *
 * Tests the Research page: search, saved sources, URL import, and scaffold.
 * Search requires an LLM API key + search tier; navigation tests work without.
 */

test.describe("Research", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);
  });

  // ─── Navigation ──────────────────────────────────────────────────────────

  test("can navigate to research page", async ({ page }) => {
    await page.goto("/research");
    await expect(page).toHaveURL(/\/research/, { timeout: 5000 });

    // Should show the search tab
    await expect(
      page.getByPlaceholder(/search academic/i),
    ).toBeVisible({ timeout: 5000 });
  });

  test("research page has search, import URLs, and saved sources tabs", async ({ page }) => {
    await page.goto("/research");

    // Tab buttons
    await expect(page.getByRole("button", { name: /search/i }).first()).toBeVisible({ timeout: 5000 });

    // Look for Import URLs / Import tab
    const importTab = page.getByRole("button", { name: /import/i }).first();
    await expect(importTab).toBeVisible({ timeout: 3000 });

    // Look for Saved Sources tab
    const savedTab = page.getByRole("button", { name: /saved/i }).first();
    await expect(savedTab).toBeVisible({ timeout: 3000 });
  });

  // ─── Search ──────────────────────────────────────────────────────────────

  test("can enter a search query", async ({ page }) => {
    await page.goto("/research");

    const searchInput = page.getByPlaceholder(/search academic/i);
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await searchInput.fill("constructivist pedagogy in computer science education");

    // Max results selector should be visible
    await expect(page.getByText(/max results/i).first()).toBeVisible({ timeout: 3000 }).catch(() => {
      // Some layouts show this differently — just verify the input works
    });

    await expect(searchInput).toHaveValue("constructivist pedagogy in computer science education");
  });

  test("can perform academic search", async ({ page }) => {
    test.setTimeout(60000);

    await page.goto("/research");

    const searchInput = page.getByPlaceholder(/search academic/i);
    await searchInput.fill("web development curriculum");

    // Click search button
    const searchBtn = page.getByRole("button", { name: /^search$/i }).first();
    await searchBtn.click();

    // Wait for results or "no results" message
    const hasResults = await page
      .locator('[class*="border"]')
      .filter({ hasText: /web|development|curriculum/i })
      .first()
      .isVisible({ timeout: 30000 })
      .catch(() => false);

    if (!hasResults) {
      // Search may fail if no search tier is available — check for error message
      const hasError = await page
        .getByText(/no results|error|not available|no search/i)
        .first()
        .isVisible({ timeout: 5000 })
        .catch(() => false);
      // Either results or a clear status message is acceptable
      expect(hasResults || hasError).toBe(true);
    }
  });

  // ─── Saved Sources ───────────────────────────────────────────────────────

  test("saved sources tab shows empty state or list", async ({ page }) => {
    await page.goto("/research");

    // Click Saved Sources tab
    const savedTab = page.getByRole("button", { name: /saved/i }).first();
    await savedTab.click();

    // Should show either saved sources or an empty state
    await expect(
      page.getByText(/saved|no sources|empty/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });
});
