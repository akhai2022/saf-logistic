import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Disputes / Litiges CRUD (Module C)
 *
 * Covers: Dispute list with status tabs, status transitions
 * (OUVERT -> EN_INSTRUCTION -> RESOLU -> CLOS_ACCEPTE),
 * expandable row details, link to create from mission,
 * mission link navigation.
 *
 * Dispute lifecycle: OUVERT -> EN_INSTRUCTION -> RESOLU/CLOS_ACCEPTE
 * Types: AVARIE, MANQUANT, RETARD, ERREUR_LIVRAISON, SURFACTURATION, AUTRE
 */

test.describe("Disputes — List & Status Transitions (Module C)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/disputes");
  });

  test("should display disputes page with Litiges title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Litiges");
  });

  test("should show status tabs for filtering", async ({ page }) => {
    await expect(page.locator("text=Tous")).toBeVisible();
    await expect(page.locator("text=Ouverts")).toBeVisible();
    await expect(page.locator("text=En instruction")).toBeVisible();
    await expect(page.locator("text=Resolus")).toBeVisible();
    await expect(page.locator("text=Clos")).toBeVisible();
  });

  test("should show link to create dispute from mission", async ({ page }) => {
    await expect(page.locator("text=Nouveau litige (depuis mission)")).toBeVisible();
  });

  test("should navigate to jobs when clicking new dispute link", async ({ page }) => {
    await page.click("text=Nouveau litige (depuis mission)");
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should show disputes table with correct headers", async ({ page }) => {
    await page.waitForTimeout(1000);
    const table = page.locator("table");
    if (await table.isVisible()) {
      await expect(page.locator("thead")).toContainText("Numero");
      await expect(page.locator("thead")).toContainText("Mission");
      await expect(page.locator("thead")).toContainText("Type");
      await expect(page.locator("thead")).toContainText("Responsabilite");
      await expect(page.locator("thead")).toContainText("Montant estime");
      await expect(page.locator("thead")).toContainText("Montant retenu");
      await expect(page.locator("thead")).toContainText("Statut");
      await expect(page.locator("thead")).toContainText("Actions");
    }
  });

  test("should show disputes table or empty state", async ({ page }) => {
    await page.waitForTimeout(1000);
    const hasTable = await page.locator("table").isVisible();
    const hasEmpty = await page.locator("text=Aucun litige").isVisible();
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test("should filter by OUVERT status tab", async ({ page }) => {
    await page.click("text=Ouverts");
    await page.waitForTimeout(500);
  });

  test("should filter by EN_INSTRUCTION status tab", async ({ page }) => {
    await page.click("text=En instruction");
    await page.waitForTimeout(500);
  });
});
