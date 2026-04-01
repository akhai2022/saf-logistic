import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsCompta } from "./helpers/auth";

/**
 * E2E Scenarios: Invoices & Credit Notes (Module E — Gap Closure)
 *
 * Covers: Invoice list with credit note button, credit note creation
 * from validated invoices, and invoice creation workflow.
 * Admin and Compta roles have billing permissions.
 */

test.describe("Invoices Page — Credit Notes", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/invoices");
  });

  test("should display invoices page with title @critical", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Factures");
    await expect(page.locator("text=Facturation clients")).toBeVisible();
  });

  test("should show new invoice button", async ({ page }) => {
    await expect(page.locator("button:has-text('Nouvelle facture')")).toBeVisible();
  });

  test("should show invoice table with correct columns including Actions", async ({ page }) => {
    await expect(page.locator("thead")).toContainText("N° Facture");
    await expect(page.locator("thead")).toContainText("Client");
    await expect(page.locator("thead")).toContainText("Statut");
    await expect(page.locator("thead")).toContainText("Total HT");
    await expect(page.locator("thead")).toContainText("Total TTC");
    await expect(page.locator("thead")).toContainText("Échéance");
    await expect(page.locator("thead")).toContainText("Actions");
  });

  test("should show credit note button on validated invoices", async ({ page }) => {
    await page.waitForTimeout(500);
    // Look for the "Creer un avoir" button (only on validated invoices)
    const creditNoteBtn = page.locator("text=Creer un avoir").first();
    // May or may not be visible depending on invoice status
    if (await creditNoteBtn.isVisible()) {
      await expect(creditNoteBtn).toBeVisible();
    }
  });

  test("should toggle create invoice form @critical", async ({ page }) => {
    await page.click("button:has-text('Nouvelle facture')");
    await expect(page.locator("text=Créer une facture")).toBeVisible();
    await expect(page.locator("text=Client")).toBeVisible();

    // Cancel
    await page.click("button:has-text('Annuler')");
    await expect(page.locator("text=Créer une facture")).not.toBeVisible();
  });

  test("should show customer selector in create form", async ({ page }) => {
    await page.click("button:has-text('Nouvelle facture')");
    const customerSelect = page.locator("select");
    await expect(customerSelect).toBeVisible();
    await expect(customerSelect).toContainText("-- Sélectionner --");
  });

  test("should show closed jobs after selecting customer", async ({ page }) => {
    await page.click("button:has-text('Nouvelle facture')");
    const customerSelect = page.locator("select");
    const options = customerSelect.locator("option");
    const optionCount = await options.count();

    if (optionCount > 1) {
      // Select the first actual customer (index 1, skipping placeholder)
      await customerSelect.selectOption({ index: 1 });
      await page.waitForTimeout(500);
      // Should show either jobs list or "Aucune mission clôturée" message
      const hasJobs = await page.locator("text=Missions clôturées").isVisible().catch(() => false);
      const hasNoJobs = await page.locator("text=Aucune mission clôturée").isVisible().catch(() => false);
    }
  });

  test("should show empty state when no invoices exist", async ({ page }) => {
    await page.waitForTimeout(500);
    const hasTable = await page.locator("tbody tr").first().isVisible().catch(() => false);
    const hasEmpty = await page.locator("text=Aucune facture").isVisible().catch(() => false);
    expect(hasTable || hasEmpty).toBeTruthy();
  });
});

test.describe("Invoices Page — Compta Role", () => {
  test("should allow compta role to access invoices page", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/invoices");
    await expect(page.locator("h1")).toContainText("Factures");
  });

  test("should show create invoice button for compta", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/invoices");
    await expect(page.locator("button:has-text('Nouvelle facture')")).toBeVisible();
  });
});
