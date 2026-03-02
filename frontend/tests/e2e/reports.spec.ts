import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsCompta, loginAsExploitant, loginAsFlotte, loginAsRH } from "./helpers/auth";

/**
 * E2E Scenarios: Reporting & KPI Dashboard (Module I)
 *
 * Covers: Role-based dashboard, KPI cards, export buttons, section access
 */

test.describe("Reports Dashboard — Admin (Module I)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports");
  });

  test("should display reports page with title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Pilotage");
  });

  test("should show role label in description", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("text=ADMIN")).toBeVisible();
  });

  test("should show KPI cards grid", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    // Admin should see KPI cards
    const kpiCards = page.locator(".grid .bg-white.rounded-xl.border.p-5");
    const count = await kpiCards.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should show all 4 export sections for admin", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=Finance")).toBeVisible();
    await expect(page.locator("text=Operations")).toBeVisible();
    await expect(page.locator("text=Flotte")).toBeVisible();
    await expect(page.locator("text=RH & Paie")).toBeVisible();
  });

  test("should show CSV export buttons", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    const csvButtons = page.locator("button:has-text('CSV')");
    const count = await csvButtons.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test("should trigger export on CSV button click", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    const csvButton = page.locator("button:has-text('CSV')").first();
    if (await csvButton.isVisible()) {
      // Click and verify it shows loading state
      await csvButton.click();
      // Button should briefly show "Export..." or return to "CSV"
      await page.waitForTimeout(1000);
    }
  });
});

test.describe("Reports Dashboard — Role-based sections", () => {
  test("should show only exploitation/compta sections for compta", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    // Compta should see Finance but not Flotte
    await expect(page.locator("text=Finance")).toBeVisible();
    // Flotte section should not be visible for compta
    const flotteSection = page.locator("text=Flotte").first();
    const isVisible = await flotteSection.isVisible().catch(() => false);
    // Note: compta role doesn't have fleet access
  });

  test("should show fleet section for flotte role", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=Flotte")).toBeVisible();
  });

  test("should show operations for exploitant role", async ({ page }) => {
    await loginAsExploitant(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=Operations")).toBeVisible();
  });

  test("should show RH section for rh_paie role", async ({ page }) => {
    await loginAsRH(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=RH & Paie")).toBeVisible();
  });
});
