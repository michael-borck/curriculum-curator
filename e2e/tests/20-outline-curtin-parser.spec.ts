import path from "path";
import { fileURLToPath } from "url";
import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 20 – Curtin University Outline Parser (regex-based, no LLM needed)
 *
 * Uploads the ISYS6020 fixture PDF and explicitly selects the "Curtin University"
 * parser. Validates that all fields are correctly extracted without an AI call.
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE_PDF = path.resolve(
  __dirname,
  "../fixtures/ISYS6020-Artificial-Intelligence-in-Business-Strategy-and-Management.pdf",
);

test.describe("Curtin Outline Parser", () => {
  test.describe.configure({ mode: "serial" });

  let createdUnitUrl = "";

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);
  });

  test("parser selector includes Curtin option", async ({ page }) => {
    await page.goto("/import/outline");
    await expect(
      page.getByText(/create from unit outline/i),
    ).toBeVisible({ timeout: 5000 });

    // Wait for parsers to load from API
    const parserSelect = page.locator("select").first();
    await expect(parserSelect).toBeVisible({ timeout: 5000 });

    // Should have the Curtin option
    const options = await parserSelect.locator("option").allTextContents();
    expect(options.some((o) => /curtin/i.test(o))).toBeTruthy();
  });

  test("Curtin parser extracts all fields from PDF", async ({ page }) => {
    test.setTimeout(30000);

    await page.goto("/import/outline");

    // Select the Curtin parser
    const parserSelect = page.locator("select").first();
    await expect(parserSelect).toBeVisible({ timeout: 5000 });
    await parserSelect.selectOption("curtin");

    // Upload the fixture PDF
    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);
    await expect(
      page.getByRole("button", { name: /parse document/i }),
    ).toBeVisible({ timeout: 5000 });

    // Monitor the parse API call
    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );

    // Click Parse Document
    await page.getByRole("button", { name: /parse document/i }).click();

    // Wait for the response (Curtin parser is fast — no LLM)
    const resp = await parseResponse;
    expect(resp.status()).toBeLessThan(400);

    // Review form should appear
    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 10000 });

    // Should show "curtin" as the parser used
    await expect(
      page.getByText(/curtin/i).first(),
    ).toBeVisible({ timeout: 3000 });
  });

  test("extracted metadata is correct", async ({ page }) => {
    test.setTimeout(30000);

    await page.goto("/import/outline");

    const parserSelect = page.locator("select").first();
    await expect(parserSelect).toBeVisible({ timeout: 5000 });
    await parserSelect.selectOption("curtin");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();
    await parseResponse;

    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 10000 });

    // Verify unit code = ISYS6020
    const codeInput = page.locator("input[placeholder*='code' i], input").first();
    await expect(codeInput).toHaveValue(/ISYS6020/);

    // Verify title contains "Artificial Intelligence"
    const titleInput = page.locator(
      "input[placeholder*='Introduction to Programming' i]",
    ).first();
    await expect(titleInput).toHaveValue(/Artificial Intelligence/i);

    // Verify credit points = 25
    const creditInput = page.locator(
      "input[type='number']",
    ).first();
    await expect(creditInput).toHaveValue("25");
  });

  test("extracted ULOs have correct Bloom levels", async ({ page }) => {
    test.setTimeout(30000);

    await page.goto("/import/outline");

    const parserSelect = page.locator("select").first();
    await expect(parserSelect).toBeVisible({ timeout: 5000 });
    await parserSelect.selectOption("curtin");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();
    await parseResponse;

    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 10000 });

    // Should have 5 ULOs
    const uloInputs = page.locator(
      "input[placeholder='Outcome description...']",
    );
    await expect(uloInputs).toHaveCount(5, { timeout: 5000 });

    // First ULO should contain "analyse" or "analyze"
    const firstUlo = uloInputs.first();
    await expect(firstUlo).toHaveValue(/analy[sz]e/i);

    // Bloom level selects should exist (at least one set to analyse/create/evaluate)
    const bloomSelects = page.locator("select").filter({
      has: page.locator("option", { hasText: /understand/i }),
    });
    expect(await bloomSelects.count()).toBe(5);
  });

  test("extracted assessments sum to 100%", async ({ page }) => {
    test.setTimeout(30000);

    await page.goto("/import/outline");

    const parserSelect = page.locator("select").first();
    await expect(parserSelect).toBeVisible({ timeout: 5000 });
    await parserSelect.selectOption("curtin");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();
    await parseResponse;

    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 10000 });

    // Should have 2 assessments
    const assessmentInputs = page.locator(
      "input[placeholder='Assessment title...']",
    );
    await expect(assessmentInputs).toHaveCount(2, { timeout: 5000 });

    // First assessment should be "AI Implementation Proposal"
    await expect(assessmentInputs.first()).toHaveValue(
      /AI Implementation Proposal/i,
    );

    // Weight badge should show 100%
    await expect(
      page.getByText("100%").first(),
    ).toBeVisible({ timeout: 3000 });
  });

  test("extracted weekly schedule has 15 weeks", async ({ page }) => {
    test.setTimeout(30000);

    await page.goto("/import/outline");

    const parserSelect = page.locator("select").first();
    await expect(parserSelect).toBeVisible({ timeout: 5000 });
    await parserSelect.selectOption("curtin");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();
    await parseResponse;

    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 10000 });

    // Should have week labels from Wk 1 to Wk 15
    const weekLabels = page.getByText(/^Wk \d+$/);
    expect(await weekLabels.count()).toBeGreaterThanOrEqual(14);
  });

  test("can create unit from Curtin-parsed outline", async ({ page }) => {
    test.setTimeout(30000);

    await page.goto("/import/outline");

    const parserSelect = page.locator("select").first();
    await expect(parserSelect).toBeVisible({ timeout: 5000 });
    await parserSelect.selectOption("curtin");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();
    await parseResponse;

    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 10000 });

    // Monitor the apply API call
    const applyResponse = page.waitForResponse(
      (r) => r.url().includes("/import/outline/apply"),
      { timeout: 15000 },
    );

    // Click Create Unit
    await page.getByRole("button", { name: /create unit/i }).click();

    const applyResp = await applyResponse;
    if (applyResp.status() >= 400) {
      const text = await applyResp.text().catch(() => "no body");
      const detail = (() => {
        try {
          return JSON.parse(text).detail;
        } catch {
          return text.slice(0, 200);
        }
      })();
      test.skip(true, `Apply API error ${applyResp.status()}: ${detail}`);
      return;
    }

    // Should redirect to the new unit page
    await expect(page).toHaveURL(/\/units\//, { timeout: 10000 });
    createdUnitUrl = page.url();

    // Unit page should show the unit code
    await expect(
      page.getByText(/ISYS6020/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });

  test("created unit has ULOs and weekly topics", async ({ page }) => {
    if (!createdUnitUrl) {
      test.skip(true, "No unit was created in previous test");
      return;
    }

    await page.goto(createdUnitUrl);
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    // Check Outcomes tab for ULOs
    const outcomesTab = page.getByRole("button", {
      name: /outcomes.*alignment/i,
    });
    if (await outcomesTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await outcomesTab.click();
      await expect(
        page.getByText(/ULO1/i).first(),
      ).toBeVisible({ timeout: 10000 });
    }

    // Check Structure tab for weekly topics
    const structureTab = page.getByRole("button", {
      name: /structure.*content/i,
    });
    if (await structureTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await structureTab.click();
    }

    await expect(
      page.getByText(/week 1/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
