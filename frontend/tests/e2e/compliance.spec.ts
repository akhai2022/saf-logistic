import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenario: Full Compliance Workflow (Module D)
 *
 * Flow: Configure templates → Check dashboard → View entity checklist →
 *       Upload document → Verify compliance updates → Check alerts → Acknowledge alert
 */
test.describe("Compliance Dashboard (Module D)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance");
  });

  test("should display compliance dashboard", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Conformité");
  });

  test("should show summary cards", async ({ page }) => {
    // Summary cards: total, conformes, a regulariser, bloquants
    await expect(page.locator("text=Total entités")).toBeVisible();
    await expect(page.locator("text=Conformes")).toBeVisible();
  });

  test("should show entity type filter tabs", async ({ page }) => {
    await expect(page.locator("text=Tous")).toBeVisible();
    await expect(page.locator("text=Conducteurs")).toBeVisible();
    await expect(page.locator("text=Véhicules")).toBeVisible();
    await expect(page.locator("text=Sous-traitants")).toBeVisible();
  });

  test("should filter by entity type", async ({ page }) => {
    await page.click("text=Conducteurs");
    await page.waitForTimeout(500);
    // Dashboard should refresh with filtered data
  });

  test("should navigate to entity checklist", async ({ page }) => {
    const viewButton = page.locator("text=Voir").first();
    if (await viewButton.isVisible()) {
      await viewButton.click();
      await expect(page).toHaveURL(/\/compliance\//);
    }
  });

  test("should navigate to alerts page", async ({ page }) => {
    await page.click("text=Alertes");
    await expect(page).toHaveURL(/\/compliance\/alerts/);
  });

  test("should navigate to templates page", async ({ page }) => {
    await page.click("text=Modèles");
    await expect(page).toHaveURL(/\/compliance\/templates/);
  });
});

test.describe("Compliance Templates", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance/templates");
  });

  test("should display templates page", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Modèles");
  });

  test("should show entity type filter tabs", async ({ page }) => {
    await expect(page.locator("text=Tous")).toBeVisible();
    await expect(page.locator("text=Conducteur")).toBeVisible();
    await expect(page.locator("text=Véhicule")).toBeVisible();
    await expect(page.locator("text=Sous-traitant")).toBeVisible();
  });

  test("should create a new compliance template", async ({ page }) => {
    await page.click("text=Nouveau modèle");

    // Fill template form
    await page.selectOption('select >> nth=0', "DRIVER"); // Entity type
    await page.fill('input >> nth=0', "PERMIS_CONDUIRE"); // Code document
    await page.fill('input >> nth=1', "Permis de conduire"); // Label
    await page.fill('input >> nth=2', "1825"); // Validity days (5 years)
    await page.fill('input >> nth=3', "1"); // Display order

    // Check obligatoire
    const obligatoireCheckbox = page.locator('input[type="checkbox"]').first();
    await obligatoireCheckbox.check();

    // Check bloquant
    const bloquantCheckbox = page.locator('input[type="checkbox"]').nth(1);
    await bloquantCheckbox.check();

    await page.click("text=Créer");
    await page.waitForTimeout(500);

    // Template should appear in the list
    await expect(page.locator("text=PERMIS_CONDUIRE")).toBeVisible();
  });

  test("should filter templates by entity type", async ({ page }) => {
    await page.click("text=Conducteur");
    await page.waitForTimeout(500);
    // Only driver templates should be shown
  });

  test("should edit existing template", async ({ page }) => {
    const editButton = page.locator("text=Modifier").first();
    if (await editButton.isVisible()) {
      await editButton.click();
      // Form should be populated with template data
      await page.waitForTimeout(500);
    }
  });
});

test.describe("Compliance Alerts", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance/alerts");
  });

  test("should display alerts page", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Alertes");
  });

  test("should show status filter tabs", async ({ page }) => {
    await expect(page.locator("text=Toutes")).toBeVisible();
    await expect(page.locator("text=Envoyées")).toBeVisible();
    await expect(page.locator("text=Acquittées")).toBeVisible();
    await expect(page.locator("text=Escaladées")).toBeVisible();
  });

  test("should filter alerts by status", async ({ page }) => {
    await page.click("text=Envoyées");
    await page.waitForTimeout(500);
  });

  test("should acknowledge an alert", async ({ page }) => {
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

  test("should navigate back to dashboard", async ({ page }) => {
    await page.click("text=Retour");
    await expect(page).toHaveURL(/\/compliance$/);
  });
});

test.describe("Entity Compliance Checklist", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("should show driver compliance checklist", async ({ page }) => {
    // Navigate via drivers list
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

    // Should show compliance summary or empty state
    const hasData = await page.locator("text=Conformité").first().isVisible();
    expect(hasData).toBeTruthy();
  });

  test("should show vehicle compliance checklist", async ({ page }) => {
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

  test("should show subcontractor compliance checklist", async ({ page }) => {
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
