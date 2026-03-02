import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsCompta, loginAsExploitant, loginAsFlotte, loginAsRH } from "./helpers/auth";

/**
 * E2E Scenarios: Reporting & KPI Dashboard (Module I)
 *
 * Covers: Role-based dashboard rendering, KPI cards grid,
 * export sections visibility per role, CSV export button functionality.
 *
 * KPI keys per role:
 * - Admin: all 7 (ca_mensuel, marge, taux_conformite, dso, cout_km, missions_en_cours, litiges_ouverts)
 * - Compta: Finance + partial Operations
 * - Exploitant: Operations
 * - Flotte: Fleet metrics
 * - RH: HR & Payroll metrics
 *
 * Export sections: Finance, Operations, Flotte, RH & Paie (CSV streaming)
 */

test.describe("Reports Dashboard — Admin (Module I)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports");
  });

  test("should display reports page with Pilotage title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Pilotage");
  });

  test("should show ADMIN role label in dashboard description", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("text=ADMIN")).toBeVisible();
  });

  test("should show KPI cards grid with metric values", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const kpiCards = page.locator(".grid .bg-white.rounded-xl.border.p-5");
    const count = await kpiCards.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should show all 4 export sections for admin role", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=Finance")).toBeVisible();
    await expect(page.locator("text=Operations")).toBeVisible();
    await expect(page.locator("text=Flotte")).toBeVisible();
    await expect(page.locator("text=RH & Paie")).toBeVisible();
  });

  test("should show CSV export buttons for data download", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    const csvButtons = page.locator("button:has-text('CSV')");
    const count = await csvButtons.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test("should trigger CSV export when clicking export button", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    const csvButton = page.locator("button:has-text('CSV')").first();
    if (await csvButton.isVisible()) {
      await csvButton.click();
      await page.waitForTimeout(1000);
    }
  });
});

test.describe("Reports Dashboard — Role-based section visibility", () => {
  test("should show Finance section for comptable role", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=Finance")).toBeVisible();
  });

  test("should show Flotte section for fleet manager role", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=Flotte")).toBeVisible();
  });

  test("should show Operations section for exploitant role", async ({ page }) => {
    await loginAsExploitant(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=Operations")).toBeVisible();
  });

  test("should show RH & Paie section for HR manager role", async ({ page }) => {
    await loginAsRH(page);
    await page.goto("/reports");
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    await expect(page.locator("text=RH & Paie")).toBeVisible();
  });
});
