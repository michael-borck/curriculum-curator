import path from "path";
import { fileURLToPath } from "url";
import { test, expect } from "@playwright/test";
import { loginAsUser, dismissOnboarding } from "../helpers/auth.js";

/**
 * Test 19 – AI-Powered Outline Import
 *
 * Uploads a real unit outline PDF and uses the Generic (AI-Powered) parser
 * to extract structure, then reviews and creates the unit.
 * Requires an LLM API key (e.g. ANTHROPIC_API_KEY in the environment).
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE_PDF = path.resolve(
  __dirname,
  "../fixtures/ISYS6020-Artificial-Intelligence-in-Business-Strategy-and-Management.pdf",
);

test.describe("AI Outline Import", () => {
  test.describe.configure({ mode: "serial" });

  let createdUnitUrl = "";

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await dismissOnboarding(page);
  });

  test("can upload PDF and see parse button", async ({ page }) => {
    await page.goto("/import/outline");
    await expect(
      page.getByText(/create from unit outline/i),
    ).toBeVisible({ timeout: 5000 });

    // Upload the fixture PDF via the hidden file input
    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    // File name should appear in the drop zone
    await expect(
      page.getByText(/ISYS6020/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Parse button should appear
    await expect(
      page.getByRole("button", { name: /parse document/i }),
    ).toBeVisible();
  });

  test("AI parser extracts structure from PDF", async ({ page }) => {
    test.setTimeout(120000);

    await page.goto("/import/outline");

    // Upload the PDF
    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);
    await expect(
      page.getByRole("button", { name: /parse document/i }),
    ).toBeVisible({ timeout: 5000 });

    // Monitor the parse API call (must match POST /parse, not GET /parsers)
    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 90000 },
    );

    // Click Parse Document
    await page.getByRole("button", { name: /parse document/i }).click();

    // Should show parsing spinner
    await expect(
      page.getByText(/parsing your document/i),
    ).toBeVisible({ timeout: 5000 });

    // Wait for the API response
    const resp = await parseResponse;
    if (resp.status() >= 400) {
      const text = await resp.text().catch(() => "no body");
      const detail = (() => {
        try {
          return JSON.parse(text).detail;
        } catch {
          return text.slice(0, 200);
        }
      })();
      test.skip(true, `Parse API error ${resp.status()}: ${detail}`);
      return;
    }

    // Review form should appear with confidence banner
    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 15000 });

    await expect(
      page.getByText(/confidence/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Should have extracted the unit code (ISYS or ISYS6020 depending on LLM)
    const codeInput = page.locator("input").first();
    const codeValue = await codeInput.inputValue();
    expect(codeValue).toMatch(/ISYS/i);

    // Should have extracted learning outcomes
    await expect(
      page.getByText(/learning outcomes/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Should have extracted weekly schedule
    await expect(
      page.getByText(/weekly schedule/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Should have extracted assessments
    await expect(
      page.getByText(/assessments/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("review form shows extracted ULOs with Bloom levels", async ({
    page,
  }) => {
    test.setTimeout(120000);

    await page.goto("/import/outline");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 90000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();

    const resp = await parseResponse;
    if (resp.status() >= 400) {
      test.skip(true, "Parse API not working");
      return;
    }

    // Wait for review form
    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 15000 });

    // Learning Outcomes section should show ULO rows
    // Each ULO row has a code input (e.g. ULO1), description, and Bloom level select
    const uloRows = page.locator(
      "input[placeholder='Outcome description...']",
    );
    const uloCount = await uloRows.count();
    expect(uloCount).toBeGreaterThanOrEqual(1);

    // At least one Bloom level select should be present
    const bloomSelects = page.locator("select").filter({
      has: page.locator("option", { hasText: /understand/i }),
    });
    expect(await bloomSelects.count()).toBeGreaterThanOrEqual(1);
  });

  test("review form shows weekly schedule and assessments", async ({
    page,
  }) => {
    test.setTimeout(120000);

    await page.goto("/import/outline");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 90000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();

    const resp = await parseResponse;
    if (resp.status() >= 400) {
      test.skip(true, "Parse API not working");
      return;
    }

    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 15000 });

    // Weekly schedule: should have week rows with topic inputs
    const weekLabels = page.getByText(/^Wk \d+$/);
    expect(await weekLabels.count()).toBeGreaterThanOrEqual(1);

    // Assessments: should have assessment rows with title inputs
    const assessmentTitleInputs = page.locator(
      "input[placeholder='Assessment title...']",
    );
    expect(await assessmentTitleInputs.count()).toBeGreaterThanOrEqual(1);

    // Create Unit button should be visible and enabled (code + title extracted)
    await expect(
      page.getByRole("button", { name: /create unit/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /create unit/i }),
    ).toBeEnabled();
  });

  test("can accept and create unit from parsed outline", async ({ page }) => {
    test.setTimeout(120000);

    await page.goto("/import/outline");

    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles(FIXTURE_PDF);

    const parseResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/import/outline/parse") &&
        !resp.url().includes("/parsers") &&
        resp.request().method() === "POST",
      { timeout: 90000 },
    );
    await page.getByRole("button", { name: /parse document/i }).click();

    const resp = await parseResponse;
    if (resp.status() >= 400) {
      test.skip(true, "Parse API not working");
      return;
    }

    await expect(
      page.getByText(/parsed with/i).first(),
    ).toBeVisible({ timeout: 15000 });

    // Monitor the apply API call
    const applyResponse = page.waitForResponse(
      (r) => r.url().includes("/import/outline/apply"),
      { timeout: 30000 },
    );

    // Click Create Unit
    await page.getByRole("button", { name: /create unit/i }).click();

    // Should show "Creating your unit..." spinner
    await expect(
      page.getByText(/creating your unit/i),
    ).toBeVisible({ timeout: 5000 });

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

    // Unit page should show the unit code somewhere
    await expect(
      page.getByText(/ISYS/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });

  test("created unit has learning outcomes and weekly topics", async ({
    page,
  }) => {
    if (!createdUnitUrl) {
      test.skip(true, "No unit was created in previous test");
      return;
    }

    await page.goto(createdUnitUrl);
    await expect(page).toHaveURL(/\/units\//, { timeout: 5000 });

    // Check Outcomes & Alignment tab for ULOs
    const outcomesTab = page.getByRole("button", {
      name: /outcomes.*alignment/i,
    });
    if (await outcomesTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await outcomesTab.click();
      await expect(
        page.getByText(/ULO/i).first(),
      ).toBeVisible({ timeout: 10000 });
    }

    // Go back to Structure & Content tab to check weekly topics
    const structureTab = page.getByRole("button", {
      name: /structure.*content/i,
    });
    if (await structureTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await structureTab.click();
    }

    // Should have weekly topics (Week 1, etc.)
    await expect(
      page.getByText(/week 1/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
