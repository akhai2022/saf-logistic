import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Jobs Quick Tests (Module C)
 *
 * Covers: Basic job list display and job creation.
 * For full mission lifecycle tests see mission-lifecycle.spec.ts.
 */
test.describe("Jobs", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("should display jobs list page with Missions title @critical", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Missions");
  });

  test("should create a new job via the quick-create form", async ({ page }) => {
    await page.click("text=Nouvelle mission");
    await page.fill('input[placeholder=""]', "TEST-E2E");
    await page.click("text=Créer la mission");
    await expect(page.locator("text=TEST-E2E")).toBeVisible();
  });
});
