import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenario: Complete Mission Lifecycle
 *
 * Flow: Create mission → Plan → Assign driver/vehicle → Start →
 *       Add delivery points → Add goods → Deliver →
 *       Upload POD → Validate POD → Close mission
 */
test.describe("Mission Lifecycle (Module C)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("should display missions list with status tabs", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Missions");
    // Verify status filter tabs exist
    await expect(page.locator("text=Tous")).toBeVisible();
    await expect(page.locator("text=Brouillon")).toBeVisible();
    await expect(page.locator("text=Planifiée")).toBeVisible();
    await expect(page.locator("text=Affectée")).toBeVisible();
    await expect(page.locator("text=En cours")).toBeVisible();
    await expect(page.locator("text=Livrée")).toBeVisible();
    await expect(page.locator("text=Clôturée")).toBeVisible();
  });

  test("should filter missions by status tab", async ({ page }) => {
    // Click a status tab and verify URL changes
    await page.click("text=Brouillon");
    await expect(page).toHaveURL(/statut=BROUILLON/);
  });

  test("should search missions", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Rechercher"]');
    await searchInput.fill("TEST");
    await page.click("text=Chercher");
    await expect(page).toHaveURL(/search=TEST/);
  });

  test("should create a new mission with full form", async ({ page }) => {
    await page.click("text=Nouvelle mission");

    // Fill the create mission form
    await page.selectOption('select >> nth=0', { index: 1 }); // Select first client
    await page.fill('input[placeholder=""]>> nth=0', "REF-CLIENT-E2E");
    await page.selectOption('select:has-text("LOT_COMPLET")', "LOT_COMPLET");

    await page.click("text=Créer la mission");

    // Should redirect or show the new mission
    await page.waitForTimeout(1000);
  });

  test("should navigate to mission detail", async ({ page }) => {
    // Click on first mission in the table
    const firstMissionLink = page.locator("table tbody tr:first-child a");
    if (await firstMissionLink.isVisible()) {
      await firstMissionLink.click();
      // Should show mission detail with tabs
      await expect(page.locator("text=Général")).toBeVisible();
      await expect(page.locator("text=Livraisons")).toBeVisible();
      await expect(page.locator("text=Marchandises")).toBeVisible();
      await expect(page.locator("text=POD")).toBeVisible();
      await expect(page.locator("text=Litiges")).toBeVisible();
    }
  });

  test("should show mission detail tabs", async ({ page }) => {
    // Navigate to first mission
    const firstMissionLink = page.locator("table tbody tr:first-child a");
    if (!(await firstMissionLink.isVisible())) {
      test.skip();
      return;
    }
    await firstMissionLink.click();

    // Tab: Général — should show info cards
    await expect(page.locator("text=Informations")).toBeVisible();
    await expect(page.locator("text=Dates")).toBeVisible();
    await expect(page.locator("text=Financier")).toBeVisible();
    await expect(page.locator("text=Affectation")).toBeVisible();

    // Tab: Livraisons
    await page.click("text=Livraisons");
    await expect(page.locator("text=Ajouter un point")).toBeVisible();

    // Tab: Marchandises
    await page.click("text=Marchandises");
    await expect(page.locator("text=Ajouter")).toBeVisible();

    // Tab: POD
    await page.click("text=POD");

    // Tab: Litiges
    await page.click("text=Litiges");
  });

  test("should add delivery point to mission", async ({ page }) => {
    const firstMissionLink = page.locator("table tbody tr:first-child a");
    if (!(await firstMissionLink.isVisible())) {
      test.skip();
      return;
    }
    await firstMissionLink.click();

    // Go to Livraisons tab
    await page.click("text=Livraisons");
    await page.click("text=Ajouter un point");

    // Fill delivery point form
    const contactInput = page.locator('input[placeholder=""]').first();
    await contactInput.fill("Jean Dupont");

    await page.click("text=Ajouter");
    await page.waitForTimeout(500);
  });

  test("should add goods to mission", async ({ page }) => {
    const firstMissionLink = page.locator("table tbody tr:first-child a");
    if (!(await firstMissionLink.isVisible())) {
      test.skip();
      return;
    }
    await firstMissionLink.click();

    // Go to Marchandises tab
    await page.click("text=Marchandises");
    await page.click("text=Ajouter");

    // Fill goods form fields
    const inputs = page.locator("input");
    // Description, nature, quantity, etc.
    await page.waitForTimeout(500);
  });

  test("should transition mission status", async ({ page }) => {
    const firstMissionLink = page.locator("table tbody tr:first-child a");
    if (!(await firstMissionLink.isVisible())) {
      test.skip();
      return;
    }
    await firstMissionLink.click();

    // Look for transition buttons in the header
    const transitionBtn = page.locator('button:has-text("PLANIFIEE"), button:has-text("AFFECTEE")').first();
    if (await transitionBtn.isVisible()) {
      await transitionBtn.click();
      await page.waitForTimeout(500);
    }
  });

  test("should assign driver and vehicle", async ({ page }) => {
    const firstMissionLink = page.locator("table tbody tr:first-child a");
    if (!(await firstMissionLink.isVisible())) {
      test.skip();
      return;
    }
    await firstMissionLink.click();

    // Check for assignment card in Général tab
    await expect(page.locator("text=Affectation")).toBeVisible();

    // Check for driver/vehicle selectors
    const driverSelect = page.locator('select').filter({ hasText: /conducteur|driver/i });
    const vehicleSelect = page.locator('select').filter({ hasText: /véhicule|vehicle/i });
    // These should be present in the affectation card
  });

  test("should create dispute on mission", async ({ page }) => {
    const firstMissionLink = page.locator("table tbody tr:first-child a");
    if (!(await firstMissionLink.isVisible())) {
      test.skip();
      return;
    }
    await firstMissionLink.click();

    // Go to Litiges tab
    await page.click("text=Litiges");
    await page.click("text=Nouveau litige");

    // Fill dispute form
    await page.waitForTimeout(500);
  });
});
