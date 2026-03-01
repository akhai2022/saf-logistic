import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenario: Full Navigation & Page Access
 *
 * Verifies all 20 pages are accessible and render correctly after login.
 */
test.describe("Navigation & Page Access", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  // --- Exploitation ---

  test("should access Jobs page", async ({ page }) => {
    await page.goto("/jobs");
    await expect(page.locator("h1")).toContainText("Missions");
  });

  test("should access Disputes page", async ({ page }) => {
    await page.goto("/disputes");
    await expect(page.locator("h1")).toContainText("Litiges");
  });

  // --- Référentiels ---

  test("should access Customers page", async ({ page }) => {
    await page.goto("/customers");
    await expect(page.locator("h1")).toContainText("Clients");
  });

  test("should access Drivers page", async ({ page }) => {
    await page.goto("/drivers");
    await expect(page.locator("h1")).toContainText("Conducteurs");
  });

  test("should access Vehicles page", async ({ page }) => {
    await page.goto("/vehicles");
    await expect(page.locator("h1")).toContainText("Véhicules");
  });

  test("should access Subcontractors page", async ({ page }) => {
    await page.goto("/subcontractors");
    await expect(page.locator("h1")).toContainText("Sous-traitants");
  });

  test("should access Compliance dashboard", async ({ page }) => {
    await page.goto("/compliance");
    await expect(page.locator("h1")).toContainText("Conformité");
  });

  test("should access Compliance alerts", async ({ page }) => {
    await page.goto("/compliance/alerts");
    await expect(page.locator("h1")).toContainText("Alertes");
  });

  test("should access Compliance templates", async ({ page }) => {
    await page.goto("/compliance/templates");
    await expect(page.locator("h1")).toContainText("Modèles");
  });

  // --- Finance ---

  test("should access Invoices page", async ({ page }) => {
    await page.goto("/invoices");
    await expect(page.locator("h1")).toContainText("Factures");
  });

  test("should access Supplier Invoices page", async ({ page }) => {
    await page.goto("/supplier-invoices");
    await expect(page.locator("h1")).toContainText("Factures Fournisseurs");
  });

  test("should access Pricing page", async ({ page }) => {
    await page.goto("/pricing");
    await expect(page.locator("h1")).toContainText("Tarification");
  });

  test("should access OCR page", async ({ page }) => {
    await page.goto("/ocr");
    await expect(page.locator("h1")).toContainText("OCR");
  });

  test("should access Payroll page", async ({ page }) => {
    await page.goto("/payroll");
    await expect(page.locator("h1")).toContainText("Pré-paie");
  });

  test("should access Onboarding page", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.locator("h1")).toContainText("Configuration");
  });

  // --- Sidebar Navigation ---

  test("should show sidebar with all sections", async ({ page }) => {
    await page.goto("/jobs");

    // Exploitation section
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
    await expect(page.locator("nav >> text=Litiges")).toBeVisible();

    // Référentiels section
    await expect(page.locator("nav >> text=Clients")).toBeVisible();
    await expect(page.locator("nav >> text=Conducteurs")).toBeVisible();
    await expect(page.locator("nav >> text=Véhicules")).toBeVisible();
    await expect(page.locator("nav >> text=Sous-traitants")).toBeVisible();
    await expect(page.locator("nav >> text=Conformité")).toBeVisible();

    // Finance section
    await expect(page.locator("nav >> text=Factures")).toBeVisible();
  });

  test("should navigate via sidebar links", async ({ page }) => {
    await page.goto("/jobs");

    // Click on Conducteurs in sidebar
    await page.locator("nav >> text=Conducteurs").click();
    await expect(page).toHaveURL(/\/drivers/);
    await expect(page.locator("h1")).toContainText("Conducteurs");

    // Click on Conformité in sidebar
    await page.locator("nav >> text=Conformité").click();
    await expect(page).toHaveURL(/\/compliance/);

    // Click on Litiges in sidebar
    await page.locator("nav >> text=Litiges").click();
    await expect(page).toHaveURL(/\/disputes/);
  });
});
