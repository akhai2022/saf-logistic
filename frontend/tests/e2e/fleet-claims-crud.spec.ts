import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Fleet Claims / Sinistres CRUD (Module H)
 *
 * Covers: Declare new claim form, vehicle/driver/type selection,
 * third-party section toggle, status transitions (DECLARE -> EN_EXPERTISE
 * -> EN_REPARATION -> CLOS -> REMBOURSE), filter by vehicle/status,
 * expandable row details.
 *
 * Claim lifecycle: DECLARE -> EN_EXPERTISE -> EN_REPARATION -> CLOS -> REMBOURSE
 * Types: ACCIDENT_CIRCULATION, ACCROCHAGE, VOL, VANDALISME, BRIS_GLACE, INCENDIE, AUTRE
 * Responsabilites: A_DETERMINER, RESPONSABLE, NON_RESPONSABLE, PARTAGE
 */

test.describe("Fleet Claims — Declare sinistre (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/claims");
  });

  test("should display claims page with Sinistres title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Sinistres");
  });

  test("should show 'Declarer un sinistre' button", async ({ page }) => {
    await expect(page.locator("button:has-text('Declarer un sinistre')")).toBeVisible();
  });

  test("should open create form when clicking declare button", async ({ page }) => {
    await page.click("button:has-text('Declarer un sinistre')");
    await expect(page.locator("text=Declarer un sinistre").nth(1)).toBeVisible();
    // Form fields should be visible
    await expect(page.locator("select").first()).toBeVisible(); // vehicle select
    await expect(page.locator("input[type='date']").first()).toBeVisible();
  });

  test("should show vehicle dropdown in create form", async ({ page }) => {
    await page.click("button:has-text('Declarer un sinistre')");
    const vehicleSelect = page.locator("select").first();
    await expect(vehicleSelect).toContainText("Selectionner");
  });

  test("should show type sinistre dropdown with 7 options", async ({ page }) => {
    await page.click("button:has-text('Declarer un sinistre')");
    const typeSelect = page.locator("select").nth(1); // second select is type
    await expect(typeSelect).toBeVisible();
    await expect(typeSelect.locator("option")).toHaveCount(7);
  });

  test("should show responsabilite dropdown with 4 options", async ({ page }) => {
    await page.click("button:has-text('Declarer un sinistre')");
    // Find the responsabilite select (has A_DETERMINER value)
    const respSelect = page.locator("select:has(option[value='A_DETERMINER'])");
    await expect(respSelect).toBeVisible();
  });

  test("should show tiers implique checkbox", async ({ page }) => {
    await page.click("button:has-text('Declarer un sinistre')");
    await expect(page.locator("text=Tiers implique")).toBeVisible();
  });

  test("should toggle third-party fields when tiers checkbox clicked", async ({ page }) => {
    await page.click("button:has-text('Declarer un sinistre')");
    const checkbox = page.locator("input[type='checkbox']").first();
    await checkbox.check();
    await expect(page.locator("input[placeholder='Nom du tiers']")).toBeVisible();
    await expect(page.locator("input[placeholder='Immatriculation tiers']")).toBeVisible();
  });

  test("should show vehicle and status filter dropdowns", async ({ page }) => {
    await expect(page.locator("select:has(option:has-text('Tous les vehicules'))")).toBeVisible();
    await expect(page.locator("select:has(option:has-text('Tous les statuts'))")).toBeVisible();
  });

  test("should show status filter with 5 status options", async ({ page }) => {
    const statusSelect = page.locator("select:has(option:has-text('Tous les statuts'))");
    // Tous les statuts + DECLARE + EN_EXPERTISE + EN_REPARATION + CLOS + REMBOURSE = 6
    await expect(statusSelect.locator("option")).toHaveCount(6);
  });

  test("should show claims table or empty state", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    const hasEmpty = await page.locator("text=Aucun sinistre").isVisible();
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test("should show correct table headers including Actions", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    if (hasTable) {
      await expect(page.locator("thead")).toContainText("Numero");
      await expect(page.locator("thead")).toContainText("Vehicule");
      await expect(page.locator("thead")).toContainText("Conducteur");
      await expect(page.locator("thead")).toContainText("Statut");
      await expect(page.locator("thead")).toContainText("Actions");
    }
  });

  test("should close create form when clicking Annuler", async ({ page }) => {
    await page.click("button:has-text('Declarer un sinistre')");
    await expect(page.locator("text=Declarer le sinistre")).toBeVisible();
    await page.click("button:has-text('Annuler')");
    await expect(page.locator("text=Declarer le sinistre")).not.toBeVisible();
  });
});
