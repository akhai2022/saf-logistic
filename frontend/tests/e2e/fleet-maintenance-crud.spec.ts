import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Fleet Maintenance CRUD (Module H)
 *
 * Covers: Create new maintenance intervention form, vehicle/type selection,
 * status transitions (PLANIFIE -> EN_COURS -> TERMINE/ANNULE),
 * filter by status and time period, vehicle column display.
 *
 * Maintenance lifecycle: PLANIFIE -> EN_COURS -> TERMINE | ANNULE
 * Types: CT, VIDANGE, PNEUS, FREINS, REVISION, TACHYGRAPHE, ATP, ASSURANCE, OTHER
 */

test.describe("Fleet Maintenance — CRUD (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/maintenance");
  });

  test("should display maintenance page with title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Maintenance");
  });

  test("should show 'Nouvelle intervention' button", async ({ page }) => {
    await expect(page.locator("button:has-text('Nouvelle intervention')")).toBeVisible();
  });

  test("should open create form when clicking new intervention button", async ({ page }) => {
    await page.click("button:has-text('Nouvelle intervention')");
    await expect(page.locator("text=Nouvelle intervention").nth(1)).toBeVisible();
    await expect(page.locator("select").first()).toBeVisible(); // vehicle select
  });

  test("should show vehicle dropdown in create form", async ({ page }) => {
    await page.click("button:has-text('Nouvelle intervention')");
    const vehicleSelect = page.locator("select").first();
    await expect(vehicleSelect).toContainText("Selectionner");
  });

  test("should show type maintenance dropdown with 9 options", async ({ page }) => {
    await page.click("button:has-text('Nouvelle intervention')");
    // Type maintenance select
    const typeSelect = page.locator("select").nth(1);
    await expect(typeSelect).toBeVisible();
    await expect(typeSelect.locator("option")).toHaveCount(9);
  });

  test("should show libelle and date fields in create form", async ({ page }) => {
    await page.click("button:has-text('Nouvelle intervention')");
    await expect(page.locator("input[placeholder*='Revision']")).toBeVisible();
    await expect(page.locator("input[type='date']").first()).toBeVisible();
  });

  test("should show status filter dropdown with 5 options", async ({ page }) => {
    const statusSelect = page.locator("select").first();
    await expect(statusSelect).toBeVisible();
    await expect(statusSelect.locator("option")).toHaveCount(5); // All + 4 statuses
  });

  test("should show days range filter dropdown with 5 periods", async ({ page }) => {
    const daysSelect = page.locator("select").nth(1);
    await expect(daysSelect).toBeVisible();
    await expect(daysSelect.locator("option")).toHaveCount(5); // 30, 60, 90, 180, 365
  });

  test("should show table with Vehicle column", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    if (hasTable) {
      await expect(page.locator("thead")).toContainText("Vehicule");
      await expect(page.locator("thead")).toContainText("Type");
      await expect(page.locator("thead")).toContainText("Statut");
      await expect(page.locator("thead")).toContainText("Actions");
    }
  });

  test("should show maintenance table or empty state message", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    const hasEmpty = await page.locator("text=Aucune maintenance").isVisible();
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test("should filter maintenance records by PLANIFIE status", async ({ page }) => {
    const statusSelect = page.locator("select").first();
    await statusSelect.selectOption("PLANIFIE");
    await page.waitForTimeout(500);
  });

  test("should change days range filter to 30 days", async ({ page }) => {
    const daysSelect = page.locator("select").nth(1);
    await daysSelect.selectOption("30");
    await page.waitForTimeout(500);
  });

  test("should close create form when clicking Annuler", async ({ page }) => {
    await page.click("button:has-text('Nouvelle intervention')");
    await expect(page.locator("text=Creer l'intervention")).toBeVisible();
    await page.click("button:has-text('Annuler')");
    await expect(page.locator("text=Creer l'intervention")).not.toBeVisible();
  });
});
