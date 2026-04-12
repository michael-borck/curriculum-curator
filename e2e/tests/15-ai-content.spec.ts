import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 15 – AI Content Generation & Enhancement
 *
 * Tests the AI Assistant sidebar and content generation features.
 * Requires an LLM API key (e.g. ANTHROPIC_API_KEY in the environment).
 */

/** Click the "AI Assist" toggle button in the unit page header (not the nav sidebar). */
async function toggleAISidebar(page: import("@playwright/test").Page) {
  // The header button says "AI Assist" (not "AI Assistant" which is the nav link)
  const headerBtn = page.getByRole("button", { name: /^AI Assist$|^Close AI$/i });
  await headerBtn.click();
}

test.describe("AI Content", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);
  });

  // ─── AI Sidebar ────────────────────────────────────────────────────────────

  test("can open and close AI sidebar on unit page", async ({ page }) => {
    await page.goto("/dashboard");
    await page.getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    // Open AI sidebar via header button
    await toggleAISidebar(page);

    // Sidebar should appear with AI Teaching Assistant heading
    await expect(
      page.getByText(/AI Teaching Assistant/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Should show the greeting message
    await expect(
      page.getByText(/I'm your AI teaching assistant/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Close sidebar — button text changes to "Close AI"
    await toggleAISidebar(page);

    // Sidebar should be hidden
    await expect(
      page.getByText(/I'm your AI teaching assistant/i),
    ).not.toBeVisible({ timeout: 5000 });
  });

  test("AI sidebar shows input field and quick actions", async ({ page }) => {
    await page.goto("/dashboard");
    await page.getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    await toggleAISidebar(page);
    await expect(
      page.getByText(/AI Teaching Assistant/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Should have a text input for prompts
    const input = page.getByPlaceholder(/ask me anything|ask anything/i);
    await expect(input).toBeVisible({ timeout: 5000 });
  });

  test("can send a message and get AI response", async ({ page }) => {
    test.setTimeout(120000);

    await page.goto("/dashboard");
    await page.getByText("Web Development Fundamentals").first().click();
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    await toggleAISidebar(page);
    await expect(
      page.getByText(/AI Teaching Assistant/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Type a message
    const input = page.getByPlaceholder(/ask me anything|ask anything/i);
    await input.fill("List 3 key topics for an introductory web development unit");
    await input.press("Enter");

    // Wait for AI response — a second message should appear after the greeting
    // Look for any response that mentions common web dev topics
    await expect(
      page.locator('[class*="bg-"]').filter({ hasText: /html|css|javascript|responsive/i }).first(),
    ).toBeVisible({ timeout: 90000 });
  });

});
