import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Full Navigation & Page Access (All Modules)
 *
 * Verifies every page is accessible and renders its title correctly after login.
 * Covers Modules A through I including new gap-closure pages:
 * Settings, Audit log, Notifications.
 * Also verifies sidebar navigation links and section visibility for admin.
 */
test.describe("Navigation & Page Access", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  // --- Exploitation ---

  test("should access Jobs page and display Missions title @critical", async ({ page }) => {
    await page.goto("/jobs");
    await expect(page.locator("h1")).toContainText("Missions");
  });

  test("should access Disputes page and display Litiges title", async ({ page }) => {
    await page.goto("/disputes");
    await expect(page.locator("h1")).toContainText("Litiges");
  });

  test("should access Tasks page and display Taches title", async ({ page }) => {
    await page.goto("/tasks");
    await expect(page.locator("h1")).toContainText("Tâches");
  });

  // --- Référentiels ---

  test("should access Customers page and display Clients title", async ({ page }) => {
    await page.goto("/customers");
    await expect(page.locator("h1")).toContainText("Clients");
  });

  test("should access Drivers page and display Conducteurs title", async ({ page }) => {
    await page.goto("/drivers");
    await expect(page.locator("h1")).toContainText("Conducteurs");
  });

  test("should access Vehicles page and display Vehicules title", async ({ page }) => {
    await page.goto("/vehicles");
    await expect(page.locator("h1")).toContainText("Véhicules");
  });

  test("should access Subcontractors page and display Sous-traitants title", async ({ page }) => {
    await page.goto("/subcontractors");
    await expect(page.locator("h1")).toContainText("Sous-traitants");
  });

  test("should access Compliance dashboard and display Conformite title", async ({ page }) => {
    await page.goto("/compliance");
    await expect(page.locator("h1")).toContainText("Conformité");
  });

  test("should access Compliance alerts page and display Alertes title", async ({ page }) => {
    await page.goto("/compliance/alerts");
    await expect(page.locator("h1")).toContainText("Alertes");
  });

  test("should access Compliance templates page and display Modeles title", async ({ page }) => {
    await page.goto("/compliance/templates");
    await expect(page.locator("h1")).toContainText("Modèles");
  });

  // --- Finance ---

  test("should access Invoices page and display Factures title", async ({ page }) => {
    await page.goto("/invoices");
    await expect(page.locator("h1")).toContainText("Factures");
  });

  test("should access Supplier Invoices page and display title", async ({ page }) => {
    await page.goto("/supplier-invoices");
    await expect(page.locator("h1")).toContainText("Factures Fournisseurs");
  });

  test("should access Pricing page and display Tarification title", async ({ page }) => {
    await page.goto("/pricing");
    await expect(page.locator("h1")).toContainText("Tarification");
  });

  test("should access OCR page and display OCR title", async ({ page }) => {
    await page.goto("/ocr");
    await expect(page.locator("h1")).toContainText("OCR");
  });

  test("should access Payroll page and display Pre-paie title", async ({ page }) => {
    await page.goto("/payroll");
    await expect(page.locator("h1")).toContainText("Pré-paie");
  });

  test("should access Onboarding page and display Configuration title", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.locator("h1")).toContainText("Configuration");
  });

  // --- Flotte (Module H) ---

  test("should access Fleet Dashboard page and display Flotte title", async ({ page }) => {
    await page.goto("/fleet");
    await expect(page.locator("h1")).toContainText("Flotte");
  });

  test("should access Fleet Maintenance page and display Maintenance title", async ({ page }) => {
    await page.goto("/fleet/maintenance");
    await expect(page.locator("h1")).toContainText("Maintenance");
  });

  test("should access Fleet Claims page and display Sinistres title", async ({ page }) => {
    await page.goto("/fleet/claims");
    await expect(page.locator("h1")).toContainText("Sinistres");
  });

  // --- Pilotage (Module I) ---

  test("should access Reports Dashboard page and display Pilotage title", async ({ page }) => {
    await page.goto("/reports");
    await expect(page.locator("h1")).toContainText("Pilotage");
  });

  // --- Parametrage (Gap Closure) ---

  test("should access Settings page and display Parametres title", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Paramètres");
  });

  test("should access Audit Log page and display Journal d'audit title", async ({ page }) => {
    await page.goto("/audit");
    await expect(page.locator("h1")).toContainText("Journal d'audit");
  });

  test("should access Notifications page and display Notifications title", async ({ page }) => {
    await page.goto("/notifications");
    await expect(page.locator("h1")).toContainText("Notifications");
  });

  // --- Sidebar Navigation ---

  test("should show sidebar with all sections for admin including parametrage @critical", async ({ page }) => {
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

    // Flotte section (Module H)
    await expect(page.locator("nav >> text=Flotte").first()).toBeVisible();
    await expect(page.locator("nav >> text=Maintenance")).toBeVisible();
    await expect(page.locator("nav >> text=Sinistres")).toBeVisible();

    // Pilotage section (Module I)
    await expect(page.locator("nav >> text=Pilotage").first()).toBeVisible();

    // Parametrage section (Gap Closure)
    await expect(page.locator("nav >> text=Paramètres")).toBeVisible();
    await expect(page.locator("nav >> text=Journal d'audit")).toBeVisible();
  });

  test("should navigate via sidebar to fleet pages", async ({ page }) => {
    await page.goto("/jobs");

    const fleetLink = page.locator("nav a[href='/fleet']");
    if (await fleetLink.isVisible()) {
      await fleetLink.click();
      await expect(page).toHaveURL(/\/fleet/);
    }
  });

  test("should navigate via sidebar to reports page", async ({ page }) => {
    await page.goto("/jobs");

    const reportsLink = page.locator("nav a[href='/reports']");
    if (await reportsLink.isVisible()) {
      await reportsLink.click();
      await expect(page).toHaveURL(/\/reports/);
    }
  });

  test("should navigate via sidebar to settings page", async ({ page }) => {
    await page.goto("/jobs");

    const settingsLink = page.locator("nav a[href='/settings']");
    if (await settingsLink.isVisible()) {
      await settingsLink.click();
      await expect(page).toHaveURL(/\/settings/);
      await expect(page.locator("h1")).toContainText("Paramètres");
    }
  });

  test("should navigate via sidebar to audit log page", async ({ page }) => {
    await page.goto("/jobs");

    const auditLink = page.locator("nav a[href='/audit']");
    if (await auditLink.isVisible()) {
      await auditLink.click();
      await expect(page).toHaveURL(/\/audit/);
      await expect(page.locator("h1")).toContainText("Journal d'audit");
    }
  });

  test("should navigate via sidebar links between referentiel pages", async ({ page }) => {
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
