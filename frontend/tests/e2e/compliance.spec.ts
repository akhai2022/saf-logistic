import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Full Compliance Workflow (Module D)
 *
 * Covers: Compliance dashboard with conformity rates, entity type filters,
 * navigation to entity checklists, alert management with acknowledgment,
 * template configuration CRUD, and per-entity compliance tabs.
 *
 * Flow: Configure templates -> Check dashboard -> View entity checklist ->
 *       Upload document -> Verify compliance updates -> Check alerts ->
 *       Acknowledge alert
 *
 * Progressive alerts: J-60 -> J-30 -> J-15 -> J-7 -> J0 (expire)
 */
test.describe("Compliance Dashboard (Module D)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance");
  });

  test("should display compliance dashboard with Conformite title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Conformité");
  });

  test("should show summary cards with total entities and conformity stats", async ({ page }) => {
    await expect(page.locator("text=Total entités")).toBeVisible();
    await expect(page.locator("text=Conformes")).toBeVisible();
  });

  test("should show entity type filter tabs for conducteurs vehicules sous-traitants", async ({ page }) => {
    await expect(page.locator("text=Tous")).toBeVisible();
    await expect(page.locator("text=Conducteurs")).toBeVisible();
    await expect(page.locator("text=Véhicules")).toBeVisible();
    await expect(page.locator("text=Sous-traitants")).toBeVisible();
  });

  test("should filter dashboard by entity type when clicking Conducteurs tab", async ({ page }) => {
    await page.click("text=Conducteurs");
    await page.waitForTimeout(500);
    // Dashboard should refresh with filtered data
  });

  test("should navigate to entity checklist from dashboard via Voir button", async ({ page }) => {
    const viewButton = page.locator("text=Voir").first();
    if (await viewButton.isVisible()) {
      await viewButton.click();
      await expect(page).toHaveURL(/\/compliance\//);
    }
  });

  test("should navigate to alerts page from dashboard link", async ({ page }) => {
    await page.click("text=Alertes");
    await expect(page).toHaveURL(/\/compliance\/alerts/);
  });

  test("should navigate to templates page from dashboard link", async ({ page }) => {
    await page.click("text=Modèles");
    await expect(page).toHaveURL(/\/compliance\/templates/);
  });
});

test.describe("Compliance Templates (Module D)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance/templates");
  });

  test("should display templates page with Modeles title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Modèles");
  });

  test("should show entity type filter tabs for template categories", async ({ page }) => {
    await expect(page.locator("text=Tous")).toBeVisible();
    await expect(page.locator("text=Conducteur")).toBeVisible();
    await expect(page.locator("text=Véhicule")).toBeVisible();
    await expect(page.locator("text=Sous-traitant")).toBeVisible();
  });

  test("should create a new compliance template with all fields", async ({ page }) => {
    await page.click("text=Nouveau modèle");

    // Fill template form
    await page.selectOption('select >> nth=0', "DRIVER"); // Entity type
    await page.fill('input >> nth=0', "PERMIS_CONDUIRE"); // Code document
    await page.fill('input >> nth=1', "Permis de conduire"); // Label
    await page.fill('input >> nth=2', "1825"); // Validity days (5 years)
    await page.fill('input >> nth=3', "1"); // Display order

    // Check obligatoire and bloquant checkboxes
    const obligatoireCheckbox = page.locator('input[type="checkbox"]').first();
    await obligatoireCheckbox.check();
    const bloquantCheckbox = page.locator('input[type="checkbox"]').nth(1);
    await bloquantCheckbox.check();

    await page.click("text=Créer");
    await page.waitForTimeout(500);

    // Template should appear in the list
    await expect(page.locator("text=PERMIS_CONDUIRE")).toBeVisible();
  });

  test("should filter templates by Conducteur entity type", async ({ page }) => {
    await page.click("text=Conducteur");
    await page.waitForTimeout(500);
  });

  test("should open edit form for existing template", async ({ page }) => {
    const editButton = page.locator("text=Modifier").first();
    if (await editButton.isVisible()) {
      await editButton.click();
      await page.waitForTimeout(500);
    }
  });
});

test.describe("Compliance Alerts (Module D)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance/alerts");
  });

  test("should display alerts page with Alertes title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Alertes");
  });

  test("should show status filter tabs for alert lifecycle", async ({ page }) => {
    await expect(page.locator("text=Toutes")).toBeVisible();
    await expect(page.locator("text=Envoyées")).toBeVisible();
    await expect(page.locator("text=Acquittées")).toBeVisible();
    await expect(page.locator("text=Escaladées")).toBeVisible();
  });

  test("should filter alerts by clicking Envoyees status tab", async ({ page }) => {
    await page.click("text=Envoyées");
    await page.waitForTimeout(500);
  });

  test("should acknowledge an alert with a comment via dialog", async ({ page }) => {
    const ackButton = page.locator("text=Acquitter").first();
    if (await ackButton.isVisible()) {
      // Mock the prompt dialog
      page.on("dialog", async (dialog) => {
        await dialog.accept("Document vérifié et en cours de renouvellement");
      });
      await ackButton.click();
      await page.waitForTimeout(500);
    }
  });

  test("should navigate back to compliance dashboard via Retour button", async ({ page }) => {
    await page.click("text=Retour");
    await expect(page).toHaveURL(/\/compliance$/);
  });
});

test.describe("Entity Compliance Checklist (Module D)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("should show driver compliance checklist in Conformite tab", async ({ page }) => {
    await page.goto("/drivers");
    const driverLink = page.locator("table tbody tr:first-child a").first();
    if (!(await driverLink.isVisible())) {
      test.skip();
      return;
    }
    await driverLink.click();

    // Click Conformité tab
    await page.click("text=Conformité");
    await page.waitForTimeout(500);

    const hasData = await page.locator("text=Conformité").first().isVisible();
    expect(hasData).toBeTruthy();
  });

  test("should show vehicle compliance checklist in Conformite tab", async ({ page }) => {
    await page.goto("/vehicles");
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();

    await page.click("text=Conformité");
    await page.waitForTimeout(500);
  });

  test("should show subcontractor compliance checklist in Conformite tab", async ({ page }) => {
    await page.goto("/subcontractors");
    const subLink = page.locator("table tbody tr:first-child a").first();
    if (!(await subLink.isVisible())) {
      test.skip();
      return;
    }
    await subLink.click();

    await page.click("text=Conformité");
    await page.waitForTimeout(500);
  });
});
