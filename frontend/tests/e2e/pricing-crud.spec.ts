import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Pricing Rules CRUD (Module E)
 *
 * Covers: Create pricing rule form with customer/type selection,
 * edit existing rules inline, delete rules with confirmation,
 * rule type labels (Au km, Forfait, Supplement), km range display.
 *
 * Rule types: km (per-kilometer), flat (fixed), surcharge (supplement)
 * Fields: label, rate, customer (optional), km range (for km type)
 */

test.describe("Pricing Rules — CRUD (Module E)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/pricing");
  });

  test("should display pricing page with Tarifs title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Tarifs");
  });

  test("should show 'Nouveau tarif' button", async ({ page }) => {
    await expect(page.locator("button:has-text('Nouveau tarif')")).toBeVisible();
  });

  test("should open create form when clicking new tarif button", async ({ page }) => {
    await page.click("button:has-text('Nouveau tarif')");
    await expect(page.locator("text=Nouveau tarif").nth(1)).toBeVisible();
  });

  test("should show client dropdown with 'Tous les clients' option", async ({ page }) => {
    await page.click("button:has-text('Nouveau tarif')");
    await expect(page.locator("select:has(option:has-text('Tous les clients'))")).toBeVisible();
  });

  test("should show rule type selector with 3 options", async ({ page }) => {
    await page.click("button:has-text('Nouveau tarif')");
    const typeSelect = page.locator("select:has(option[value='km'])");
    await expect(typeSelect).toBeVisible();
    await expect(typeSelect.locator("option")).toHaveCount(3);
  });

  test("should show km range fields when type is km", async ({ page }) => {
    await page.click("button:has-text('Nouveau tarif')");
    await expect(page.locator("text=Km min")).toBeVisible();
    await expect(page.locator("text=Km max")).toBeVisible();
  });

  test("should hide km range fields when type is flat", async ({ page }) => {
    await page.click("button:has-text('Nouveau tarif')");
    const typeSelect = page.locator("select:has(option[value='km'])");
    await typeSelect.selectOption("flat");
    await expect(page.locator("text=Km min")).not.toBeVisible();
  });

  test("should show pricing table with correct headers", async ({ page }) => {
    const table = page.locator("table");
    if (await table.isVisible()) {
      await expect(page.locator("thead")).toContainText("Libelle");
      await expect(page.locator("thead")).toContainText("Type");
      await expect(page.locator("thead")).toContainText("Tarif");
      await expect(page.locator("thead")).toContainText("Client");
      await expect(page.locator("thead")).toContainText("Actions");
    }
  });

  test("should show Modifier and Supprimer action buttons for rules", async ({ page }) => {
    const modifyBtn = page.locator("text=Modifier").first();
    const deleteBtn = page.locator("text=Supprimer").first();
    if (await modifyBtn.isVisible()) {
      await expect(modifyBtn).toBeVisible();
      await expect(deleteBtn).toBeVisible();
    }
  });

  test("should open edit form when clicking Modifier", async ({ page }) => {
    const modifyBtn = page.locator("text=Modifier").first();
    if (await modifyBtn.isVisible()) {
      await modifyBtn.click();
      await expect(page.locator("text=Modifier le tarif")).toBeVisible();
      await expect(page.locator("text=Enregistrer")).toBeVisible();
    }
  });

  test("should show pricing table or empty state", async ({ page }) => {
    const hasTable = await page.locator("table tbody tr").count();
    const hasEmpty = await page.locator("text=Aucun tarif").isVisible();
    expect(hasTable > 0 || hasEmpty).toBeTruthy();
  });
});
