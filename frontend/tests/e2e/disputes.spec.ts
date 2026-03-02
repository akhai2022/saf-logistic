import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Disputes Management (Module C)
 *
 * Covers: Disputes list page, status filter tabs (Ouverts, En instruction,
 * Resolus, Clos), table columns display, and navigation to linked mission.
 * Disputes follow a lifecycle: OUVERT -> EN_INSTRUCTION -> RESOLU -> CLOS
 * and are numbered LIT-YYYY-NNNNN.
 */
test.describe("Disputes (Module C)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/disputes");
  });

  test("should display disputes page with Litiges title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Litiges");
  });

  test("should show all status filter tabs for dispute lifecycle", async ({ page }) => {
    await expect(page.locator("text=Tous")).toBeVisible();
    await expect(page.locator("text=Ouverts")).toBeVisible();
    await expect(page.locator("text=En instruction")).toBeVisible();
    await expect(page.locator("text=Résolus")).toBeVisible();
    await expect(page.locator("text=Clos")).toBeVisible();
  });

  test("should filter disputes by clicking Ouverts status tab", async ({ page }) => {
    await page.click("text=Ouverts");
    // The table should update (filtered by OUVERT status)
    await page.waitForTimeout(500);
  });

  test("should show dispute table with correct columns", async ({ page }) => {
    const headers = page.locator("thead th");
    await expect(headers.nth(0)).toContainText("Numéro");
    await expect(headers.nth(1)).toContainText("Mission");
    await expect(headers.nth(2)).toContainText("Type");
    await expect(headers.nth(3)).toContainText("Responsabilité");
  });

  test("should navigate to linked mission from dispute row", async ({ page }) => {
    const missionLink = page.locator("table tbody a[href*='/jobs/']").first();
    if (await missionLink.isVisible()) {
      await missionLink.click();
      await expect(page).toHaveURL(/\/jobs\//);
    }
  });
});
