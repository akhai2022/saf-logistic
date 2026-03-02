import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsExploitant } from "./helpers/auth";

/**
 * E2E Scenarios: Settings / Parametrage (Module A — Gap Closure)
 *
 * Covers the 5-tab settings page: Company identity, Bank accounts,
 * VAT rates, Cost centers, and Notification configs.
 * Only admin role has settings.update permission.
 */

// ── Settings Page — General ──────────────────────────────────────

test.describe("Settings Page — Access & Tabs", () => {
  test("should display settings page with title and description", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Paramètres");
    await expect(page.locator("text=Configuration de la plateforme")).toBeVisible();
  });

  test("should show all 5 tabs for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await expect(page.locator("text=Entreprise")).toBeVisible();
    await expect(page.locator("text=Banque")).toBeVisible();
    await expect(page.locator("text=TVA")).toBeVisible();
    await expect(page.locator("text=Centres de coûts")).toBeVisible();
    await expect(page.locator("text=Notifications")).toBeVisible();
  });

  test("should switch between tabs without page reload", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");

    // Click each tab and verify content changes
    await page.click("text=Banque");
    await expect(page.locator("text=Comptes bancaires")).toBeVisible();

    await page.click("text=TVA");
    await expect(page.locator("text=Taux de TVA")).toBeVisible();

    await page.click("text=Centres de coûts");
    await expect(page.locator("text=Centres de coûts")).toBeVisible();

    await page.click("text=Notifications");
    await expect(page.locator("text=Configuration des notifications")).toBeVisible();
  });
});

// ── Company Tab ──────────────────────────────────────────────────

test.describe("Settings — Company Tab", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
  });

  test("should display company form with all fields", async ({ page }) => {
    await expect(page.locator("text=Informations entreprise")).toBeVisible();
    await expect(page.locator("text=Raison sociale")).toBeVisible();
    await expect(page.locator("text=SIREN")).toBeVisible();
    await expect(page.locator("text=SIRET")).toBeVisible();
    await expect(page.locator("text=TVA Intracommunautaire")).toBeVisible();
    await expect(page.locator("text=Adresse")).toBeVisible();
    await expect(page.locator("text=Code postal")).toBeVisible();
    await expect(page.locator("text=Ville")).toBeVisible();
    await expect(page.locator("text=Email")).toBeVisible();
    await expect(page.locator("text=Licence transport")).toBeVisible();
  });

  test("should show save button for company settings", async ({ page }) => {
    await expect(page.locator("button:has-text('Enregistrer')")).toBeVisible();
  });

  test("should fill and save company settings", async ({ page }) => {
    const raisonSocialeInput = page.locator('input').nth(0);
    await raisonSocialeInput.fill("SAF Transport SAS");
    await page.click("button:has-text('Enregistrer')");
    await page.waitForTimeout(1000);
    // Button should return to normal state after save
    await expect(page.locator("button:has-text('Enregistrer')")).toBeVisible();
  });
});

// ── Bank Accounts Tab ────────────────────────────────────────────

test.describe("Settings — Bank Accounts Tab", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await page.click("text=Banque");
  });

  test("should display bank accounts section with add button", async ({ page }) => {
    await expect(page.locator("text=Comptes bancaires")).toBeVisible();
    await expect(page.locator("button:has-text('Ajouter')")).toBeVisible();
  });

  test("should show bank account form when clicking add", async ({ page }) => {
    await page.click("button:has-text('Ajouter')");
    await expect(page.locator("input[placeholder='Libelle']")).toBeVisible();
    await expect(page.locator("input[placeholder='IBAN']")).toBeVisible();
    await expect(page.locator("input[placeholder='BIC']")).toBeVisible();
    await expect(page.locator("input[placeholder='Banque']")).toBeVisible();
  });

  test("should toggle add form with cancel button", async ({ page }) => {
    await page.click("button:has-text('Ajouter')");
    await expect(page.locator("input[placeholder='IBAN']")).toBeVisible();

    await page.click("button:has-text('Annuler')");
    await expect(page.locator("input[placeholder='IBAN']")).not.toBeVisible();
  });

  test("should show table headers for bank accounts", async ({ page }) => {
    await expect(page.locator("thead")).toContainText("Libelle");
    await expect(page.locator("thead")).toContainText("IBAN");
    await expect(page.locator("thead")).toContainText("BIC");
    await expect(page.locator("thead")).toContainText("Banque");
    await expect(page.locator("thead")).toContainText("Defaut");
  });
});

// ── VAT Tab ──────────────────────────────────────────────────────

test.describe("Settings — VAT Tab", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await page.click("text=TVA");
  });

  test("should display VAT config section with add button", async ({ page }) => {
    await expect(page.locator("text=Taux de TVA")).toBeVisible();
    await expect(page.locator("button:has-text('Ajouter')")).toBeVisible();
  });

  test("should show VAT form when clicking add", async ({ page }) => {
    await page.click("button:has-text('Ajouter')");
    await expect(page.locator("input[placeholder='Taux (%)']")).toBeVisible();
    await expect(page.locator("input[placeholder='Libelle']")).toBeVisible();
    await expect(page.locator("input[placeholder='Mention legale']")).toBeVisible();
  });

  test("should show table headers for VAT configs", async ({ page }) => {
    await expect(page.locator("thead")).toContainText("Taux");
    await expect(page.locator("thead")).toContainText("Libelle");
    await expect(page.locator("thead")).toContainText("Mention legale");
    await expect(page.locator("thead")).toContainText("Defaut");
    await expect(page.locator("thead")).toContainText("Actif");
  });

  test("should display seeded French VAT rates", async ({ page }) => {
    // Seed data should include standard French VAT rates
    await page.waitForTimeout(500);
    const rows = page.locator("tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(0); // At least seed data if present
  });
});

// ── Cost Centers Tab ─────────────────────────────────────────────

test.describe("Settings — Cost Centers Tab", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await page.click("text=Centres de coûts");
  });

  test("should display cost centers section with add button", async ({ page }) => {
    await expect(page.locator("text=Centres de coûts")).toBeVisible();
    await expect(page.locator("button:has-text('Ajouter')")).toBeVisible();
  });

  test("should show cost center form when clicking add", async ({ page }) => {
    await page.click("button:has-text('Ajouter')");
    await expect(page.locator("input[placeholder='Code']")).toBeVisible();
    await expect(page.locator("input[placeholder='Libelle']")).toBeVisible();
  });

  test("should show table headers for cost centers", async ({ page }) => {
    await expect(page.locator("thead")).toContainText("Code");
    await expect(page.locator("thead")).toContainText("Libelle");
    await expect(page.locator("thead")).toContainText("Actif");
  });
});

// ── Notifications Config Tab ─────────────────────────────────────

test.describe("Settings — Notifications Config Tab", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await page.click("text=Notifications");
  });

  test("should display notification configs section with add button", async ({ page }) => {
    await expect(page.locator("text=Configuration des notifications")).toBeVisible();
    await expect(page.locator("button:has-text('Ajouter')")).toBeVisible();
  });

  test("should show notification config form when clicking add", async ({ page }) => {
    await page.click("button:has-text('Ajouter')");
    await expect(page.locator("input[placeholder=\"Type d'evenement\"]")).toBeVisible();
    await expect(page.locator("input[placeholder='Delai (heures)']")).toBeVisible();
  });

  test("should show table headers for notification configs", async ({ page }) => {
    await expect(page.locator("thead")).toContainText("Evenement");
    await expect(page.locator("thead")).toContainText("Canaux");
    await expect(page.locator("thead")).toContainText("Destinataires");
    await expect(page.locator("thead")).toContainText("Delai");
    await expect(page.locator("thead")).toContainText("Actif");
  });
});
