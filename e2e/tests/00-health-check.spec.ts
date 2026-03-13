import { test, expect } from "@playwright/test";

test.describe("Health Check", () => {
  test("backend API responds", async ({ request }) => {
    const response = await request.get("http://localhost:8000/api/auth/config");
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty("hasUsers");
  });

  test("frontend loads", async ({ page }) => {
    await page.goto("/");
    // Landing page should show the app title in the nav bar
    await expect(
      page.getByRole("navigation").getByText("Curriculum Curator"),
    ).toBeVisible();
  });

  test("landing page has sign in button", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("button", { name: /sign in/i }),
    ).toBeVisible();
  });
});
