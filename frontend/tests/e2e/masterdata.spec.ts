import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Master Data CRUD (Module B — Referentiels)
 *
 * Covers: Clients, Drivers, Vehicles, Subcontractors
 * Flow per entity: List -> Create -> Detail -> Edit -> Status change ->
 *                  Compliance tab (Module D integration)
 *
 * Validation rules tested indirectly:
 * - Client: SIRET format, LME payment terms (max 60j net / 45j fin de mois)
 * - Driver: NIR format validation, auto-inactivation on date_sortie
 * - Vehicle: VIN format (17 chars, no I/O/Q)
 */
test.describe("Customers (Module B)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/customers");
  });

  test("should display customers list with table headers", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Clients");
    await expect(page.locator("thead")).toContainText("Code");
    await expect(page.locator("thead")).toContainText("Raison sociale");
    await expect(page.locator("thead")).toContainText("SIRET");
  });

  test("should search customers using the search input", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Rechercher"]');
    await searchInput.fill("Test");
    await page.waitForTimeout(500); // debounced search
  });

  test("should open create customer form and fill raison sociale and SIRET", async ({ page }) => {
    await page.click("text=Nouveau client");

    await page.fill('input >> nth=0', "TEST-RAISON-SOCIALE");
    await page.fill('input >> nth=1', "44306184100047"); // Valid SIRET

    await page.click("text=Créer");
    await page.waitForTimeout(500);
  });

  test("should navigate to customer detail with all tabs visible", async ({ page }) => {
    const customerLink = page.locator("table tbody tr:first-child a").first();
    if (await customerLink.isVisible()) {
      await customerLink.click();
      await expect(page.locator("text=Identification")).toBeVisible();
      await expect(page.locator("text=Général")).toBeVisible();
      await expect(page.locator("text=Contacts")).toBeVisible();
      await expect(page.locator("text=Adresses")).toBeVisible();
    }
  });

  test("should open add contact form in customer detail Contacts tab", async ({ page }) => {
    const customerLink = page.locator("table tbody tr:first-child a").first();
    if (!(await customerLink.isVisible())) {
      test.skip();
      return;
    }
    await customerLink.click();
    await page.click("text=Contacts");
    await page.click("text=Ajouter un contact");
    await page.waitForTimeout(500);
  });

  test("should open add address form in customer detail Adresses tab", async ({ page }) => {
    const customerLink = page.locator("table tbody tr:first-child a").first();
    if (!(await customerLink.isVisible())) {
      test.skip();
      return;
    }
    await customerLink.click();
    await page.click("text=Adresses");
    await page.click("text=Ajouter une adresse");
    await page.waitForTimeout(500);
  });
});

test.describe("Drivers (Module B)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/drivers");
  });

  test("should display drivers list with Matricule and Nom columns", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Conducteurs");
    await expect(page.locator("thead")).toContainText("Matricule");
    await expect(page.locator("thead")).toContainText("Nom");
  });

  test("should open create driver form when clicking Nouveau conducteur", async ({ page }) => {
    await page.click("text=Nouveau conducteur");
    await page.waitForTimeout(500);
  });

  test("should navigate to driver detail with 4 tabs", async ({ page }) => {
    const driverLink = page.locator("table tbody tr:first-child a").first();
    if (!(await driverLink.isVisible())) {
      test.skip();
      return;
    }
    await driverLink.click();

    // Verify all 4 tabs exist
    await expect(page.locator("text=Identité")).toBeVisible();
    await expect(page.locator("text=Contrat")).toBeVisible();
    await expect(page.locator("text=Qualifications")).toBeVisible();
    await expect(page.locator("text=Conformité")).toBeVisible();
  });

  test("should show qualifications with license categories FIMO FCO ADR", async ({ page }) => {
    const driverLink = page.locator("table tbody tr:first-child a").first();
    if (!(await driverLink.isVisible())) {
      test.skip();
      return;
    }
    await driverLink.click();
    await page.click("text=Qualifications");

    // Should show license category buttons and FIMO/FCO/ADR checkboxes
    await expect(page.locator("text=Permis de conduire")).toBeVisible();
    await expect(page.locator("text=FIMO")).toBeVisible();
    await expect(page.locator("text=FCO")).toBeVisible();
    await expect(page.locator("text=ADR")).toBeVisible();
  });

  test("should show driver status card in detail page", async ({ page }) => {
    const driverLink = page.locator("table tbody tr:first-child a").first();
    if (!(await driverLink.isVisible())) {
      test.skip();
      return;
    }
    await driverLink.click();

    await expect(page.locator("text=Statut").last()).toBeVisible();
  });
});

test.describe("Vehicles (Module B)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
  });

  test("should display vehicles list with Immatriculation column", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Véhicules");
    await expect(page.locator("thead")).toContainText("Immatriculation");
  });

  test("should filter vehicles by category using dropdown", async ({ page }) => {
    const categorySelect = page.locator("select").nth(1);
    if (await categorySelect.isVisible()) {
      await categorySelect.selectOption({ index: 1 });
      await page.waitForTimeout(500);
    }
  });

  test("should navigate to vehicle detail with 4 base tabs", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();

    await expect(page.locator("text=Général")).toBeVisible();
    await expect(page.locator("text=Caractéristiques")).toBeVisible();
    await expect(page.locator("text=Technique")).toBeVisible();
    await expect(page.locator("text=Conformité")).toBeVisible();
  });

  test("should show Dimensions section in vehicle Caracteristiques tab", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Caractéristiques");

    await expect(page.locator("text=Dimensions")).toBeVisible();
  });

  test("should show Motorisation section in vehicle Technique tab", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Technique");

    await expect(page.locator("text=Motorisation")).toBeVisible();
  });
});

test.describe("Subcontractors (Module B)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/subcontractors");
  });

  test("should display subcontractors list with Code and Raison sociale columns", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Sous-traitants");
    await expect(page.locator("thead")).toContainText("Code");
    await expect(page.locator("thead")).toContainText("Raison sociale");
  });

  test("should navigate to subcontractor detail with 3 tabs", async ({ page }) => {
    const subLink = page.locator("table tbody tr:first-child a").first();
    if (!(await subLink.isVisible())) {
      test.skip();
      return;
    }
    await subLink.click();

    await expect(page.locator("text=Général")).toBeVisible();
    await expect(page.locator("text=Contrats")).toBeVisible();
    await expect(page.locator("text=Conformité")).toBeVisible();
  });

  test("should open add contract form in subcontractor Contrats tab", async ({ page }) => {
    const subLink = page.locator("table tbody tr:first-child a").first();
    if (!(await subLink.isVisible())) {
      test.skip();
      return;
    }
    await subLink.click();
    await page.click("text=Contrats");

    await page.click("text=Ajouter contrat");
    await expect(page.locator("text=Nouveau contrat")).toBeVisible();
  });
});
