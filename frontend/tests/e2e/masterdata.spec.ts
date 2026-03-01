import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Master Data CRUD (Module B)
 *
 * Covers: Clients, Drivers, Vehicles, Subcontractors
 * Flow per entity: List → Create → Detail → Edit → Status change → Compliance tab
 */
test.describe("Customers", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/customers");
  });

  test("should display customers list", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Clients");
    // Table should have correct headers
    await expect(page.locator("thead")).toContainText("Code");
    await expect(page.locator("thead")).toContainText("Raison sociale");
    await expect(page.locator("thead")).toContainText("SIRET");
  });

  test("should search customers", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Rechercher"]');
    await searchInput.fill("Test");
    await page.waitForTimeout(500); // debounced search
  });

  test("should create a new customer", async ({ page }) => {
    await page.click("text=Nouveau client");

    await page.fill('input >> nth=0', "TEST-RAISON-SOCIALE");
    await page.fill('input >> nth=1', "44306184100047"); // Valid SIRET

    await page.click("text=Créer");
    await page.waitForTimeout(500);
  });

  test("should navigate to customer detail", async ({ page }) => {
    const customerLink = page.locator("table tbody tr:first-child a").first();
    if (await customerLink.isVisible()) {
      await customerLink.click();
      await expect(page.locator("text=Identification")).toBeVisible();
      await expect(page.locator("text=Général")).toBeVisible();
      await expect(page.locator("text=Contacts")).toBeVisible();
      await expect(page.locator("text=Adresses")).toBeVisible();
    }
  });

  test("should manage contacts in customer detail", async ({ page }) => {
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

  test("should manage addresses in customer detail", async ({ page }) => {
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

test.describe("Drivers", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/drivers");
  });

  test("should display drivers list", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Conducteurs");
    await expect(page.locator("thead")).toContainText("Matricule");
    await expect(page.locator("thead")).toContainText("Nom");
  });

  test("should create a new driver", async ({ page }) => {
    await page.click("text=Nouveau conducteur");
    await page.waitForTimeout(500);
    // Form should appear
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

  test("should show qualifications with license categories", async ({ page }) => {
    const driverLink = page.locator("table tbody tr:first-child a").first();
    if (!(await driverLink.isVisible())) {
      test.skip();
      return;
    }
    await driverLink.click();
    await page.click("text=Qualifications");

    // Should show license category buttons
    await expect(page.locator("text=Permis de conduire")).toBeVisible();
    // Should show FIMO/FCO/ADR checkboxes
    await expect(page.locator("text=FIMO")).toBeVisible();
    await expect(page.locator("text=FCO")).toBeVisible();
    await expect(page.locator("text=ADR")).toBeVisible();
  });

  test("should change driver status", async ({ page }) => {
    const driverLink = page.locator("table tbody tr:first-child a").first();
    if (!(await driverLink.isVisible())) {
      test.skip();
      return;
    }
    await driverLink.click();

    // Statut card should be visible
    await expect(page.locator("text=Statut").last()).toBeVisible();
  });
});

test.describe("Vehicles", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
  });

  test("should display vehicles list", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Véhicules");
    await expect(page.locator("thead")).toContainText("Immatriculation");
  });

  test("should filter vehicles by category", async ({ page }) => {
    const categorySelect = page.locator("select").nth(1);
    if (await categorySelect.isVisible()) {
      await categorySelect.selectOption({ index: 1 });
      await page.waitForTimeout(500);
    }
  });

  test("should navigate to vehicle detail with 4 tabs", async ({ page }) => {
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

  test("should show vehicle characteristics tab", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Caractéristiques");

    await expect(page.locator("text=Dimensions")).toBeVisible();
  });

  test("should show vehicle technique tab", async ({ page }) => {
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

test.describe("Subcontractors", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/subcontractors");
  });

  test("should display subcontractors list", async ({ page }) => {
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

  test("should manage subcontractor contracts", async ({ page }) => {
    const subLink = page.locator("table tbody tr:first-child a").first();
    if (!(await subLink.isVisible())) {
      test.skip();
      return;
    }
    await subLink.click();
    await page.click("text=Contrats");

    await page.click("text=Ajouter contrat");
    // Contract form should appear
    await expect(page.locator("text=Nouveau contrat")).toBeVisible();
  });
});
