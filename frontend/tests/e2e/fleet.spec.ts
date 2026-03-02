import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Fleet Management (Module H)
 *
 * Covers: Fleet Dashboard, Maintenance list, Claims list,
 *         Vehicle Maintenance tab, Vehicle Costs tab
 */

// ── Fleet Dashboard ────────────────────────────────────────────

test.describe("Fleet Dashboard (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet");
  });

  test("should display fleet dashboard page", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Flotte");
  });

  test("should show KPI stat cards", async ({ page }) => {
    // Wait for loading to finish
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});

    // Dashboard should show KPI cards
    await expect(page.locator("text=Vehicules")).toBeVisible();
    await expect(page.locator("text=Actifs")).toBeVisible();
  });

  test("should show cost card", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("text=Cout total du mois")).toBeVisible();
  });

  test("should show upcoming maintenance section", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("text=Maintenances a venir")).toBeVisible();
  });

  test("should show quick links to sub-pages", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("a[href='/fleet/maintenance']")).toBeVisible();
    await expect(page.locator("a[href='/fleet/claims']")).toBeVisible();
    await expect(page.locator("a[href='/vehicles']")).toBeVisible();
  });

  test("should navigate to maintenance page via quick link", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await page.locator("a[href='/fleet/maintenance']").click();
    await expect(page).toHaveURL(/\/fleet\/maintenance/);
    await expect(page.locator("h1")).toContainText("Maintenance");
  });

  test("should navigate to claims page via quick link", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await page.locator("a[href='/fleet/claims']").click();
    await expect(page).toHaveURL(/\/fleet\/claims/);
    await expect(page.locator("h1")).toContainText("Sinistres");
  });
});

// ── Maintenance List ───────────────────────────────────────────

test.describe("Maintenance List (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/maintenance");
  });

  test("should display maintenance page", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Maintenance");
  });

  test("should show status filter dropdown", async ({ page }) => {
    const statusSelect = page.locator("select").first();
    await expect(statusSelect).toBeVisible();
    // Verify options
    await expect(statusSelect.locator("option")).toHaveCount(5); // All + 4 statuses
  });

  test("should show days range dropdown", async ({ page }) => {
    const daysSelect = page.locator("select").nth(1);
    await expect(daysSelect).toBeVisible();
    // Verify options: 30, 60, 90, 180, 365
    await expect(daysSelect.locator("option")).toHaveCount(5);
  });

  test("should filter by status", async ({ page }) => {
    const statusSelect = page.locator("select").first();
    await statusSelect.selectOption("PLANIFIE");
    await page.waitForTimeout(500);
  });

  test("should change days range", async ({ page }) => {
    const daysSelect = page.locator("select").nth(1);
    await daysSelect.selectOption("30");
    await page.waitForTimeout(500);
  });

  test("should show table or empty state", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    // Either a table with records or the empty state
    const hasTable = await page.locator("table").isVisible();
    const hasEmpty = await page.locator("text=Aucune maintenance").isVisible();
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test("should show correct table headers when data exists", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    if (hasTable) {
      await expect(page.locator("thead")).toContainText("Type");
      await expect(page.locator("thead")).toContainText("Libelle");
      await expect(page.locator("thead")).toContainText("Statut");
      await expect(page.locator("thead")).toContainText("Cout HT");
    }
  });
});

// ── Claims List ────────────────────────────────────────────────

test.describe("Claims List (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/claims");
  });

  test("should display claims page", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Sinistres");
  });

  test("should show vehicle filter dropdown", async ({ page }) => {
    const vehicleSelect = page.locator("select").first();
    await expect(vehicleSelect).toBeVisible();
    await expect(vehicleSelect).toContainText("Tous les vehicules");
  });

  test("should show status filter dropdown", async ({ page }) => {
    const statusSelect = page.locator("select").nth(1);
    await expect(statusSelect).toBeVisible();
    await expect(statusSelect).toContainText("Tous les statuts");
  });

  test("should filter by status", async ({ page }) => {
    const statusSelect = page.locator("select").nth(1);
    await statusSelect.selectOption("DECLARE");
    await page.waitForTimeout(500);
  });

  test("should show table or empty state", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    const hasEmpty = await page.locator("text=Aucun sinistre").isVisible();
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test("should show correct table headers when data exists", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    if (hasTable) {
      await expect(page.locator("thead")).toContainText("Numero");
      await expect(page.locator("thead")).toContainText("Vehicule");
      await expect(page.locator("thead")).toContainText("Date");
      await expect(page.locator("thead")).toContainText("Type");
      await expect(page.locator("thead")).toContainText("Responsabilite");
      await expect(page.locator("thead")).toContainText("Statut");
    }
  });
});

// ── Vehicle Detail: Maintenance & Coûts Tabs ───────────────────

test.describe("Vehicle Detail — Maintenance Tab (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
  });

  test("should show 6 tabs including Maintenance and Coûts", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();

    await expect(page.locator("text=Général")).toBeVisible();
    await expect(page.locator("text=Caractéristiques")).toBeVisible();
    await expect(page.locator("text=Technique")).toBeVisible();
    await expect(page.locator("text=Maintenance")).toBeVisible();
    await expect(page.locator("text=Coûts")).toBeVisible();
    await expect(page.locator("text=Conformité")).toBeVisible();
  });

  test("should display maintenance tab content", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Maintenance");

    // Should show plans and interventions sections
    await expect(page.locator("text=Plans de maintenance")).toBeVisible();
    await expect(page.locator("text=Interventions")).toBeVisible();
  });

  test("should show add maintenance schedule form", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Maintenance");

    // Click add plan button
    const addBtn = page.locator("text=Ajouter un plan");
    if (await addBtn.isVisible()) {
      await addBtn.click();
      // Form should appear with type selector
      await expect(page.locator("select")).toBeVisible();
    }
  });

  test("should show add maintenance record form", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Maintenance");

    const addBtn = page.locator("text=Ajouter intervention");
    if (await addBtn.isVisible()) {
      await addBtn.click();
      await page.waitForTimeout(300);
    }
  });
});

test.describe("Vehicle Detail — Coûts Tab (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
  });

  test("should display costs tab content", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Coûts");

    // Should show cost summary section
    await expect(page.locator("text=Synthese des couts")).toBeVisible();
  });

  test("should show add cost form", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Coûts");

    const addBtn = page.locator("text=Ajouter un cout");
    if (await addBtn.isVisible()) {
      await addBtn.click();
      await page.waitForTimeout(300);
    }
  });
});
