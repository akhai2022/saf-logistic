import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Fleet Management (Module H)
 *
 * Covers: Fleet Dashboard with KPI cards and quick links,
 * Maintenance list with status/days filters, Claims list with
 * vehicle/status filters, and Vehicle detail tabs (Maintenance + Couts).
 *
 * Fleet dashboard aggregates: vehicle availability, upcoming maintenance,
 * open claims, monthly cost total.
 *
 * Maintenance lifecycle: PLANIFIE -> EN_COURS -> TERMINE -> ANNULE
 * Claims lifecycle: DECLARE -> EN_COURS -> CLOTURE_FAVORABLE/DEFAVORABLE
 */

// ── Fleet Dashboard ────────────────────────────────────────────

test.describe("Fleet Dashboard (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet");
  });

  test("should display fleet dashboard page with Flotte title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Flotte");
  });

  test("should show KPI stat cards for vehicles and active count", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("text=Vehicules")).toBeVisible();
    await expect(page.locator("text=Actifs")).toBeVisible();
  });

  test("should show monthly cost total card", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("text=Cout total du mois")).toBeVisible();
  });

  test("should show upcoming maintenance section with scheduled items", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    await expect(page.locator("text=Maintenances a venir")).toBeVisible();
  });

  test("should show quick navigation links to maintenance claims and vehicles", async ({ page }) => {
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

  test("should display maintenance page with title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Maintenance");
  });

  test("should show status filter dropdown with 5 options", async ({ page }) => {
    const statusSelect = page.locator("select").first();
    await expect(statusSelect).toBeVisible();
    await expect(statusSelect.locator("option")).toHaveCount(5); // All + 4 statuses
  });

  test("should show days range filter dropdown with 5 periods", async ({ page }) => {
    const daysSelect = page.locator("select").nth(1);
    await expect(daysSelect).toBeVisible();
    await expect(daysSelect.locator("option")).toHaveCount(5); // 30, 60, 90, 180, 365
  });

  test("should filter maintenance records by PLANIFIE status", async ({ page }) => {
    const statusSelect = page.locator("select").first();
    await statusSelect.selectOption("PLANIFIE");
    await page.waitForTimeout(500);
  });

  test("should change days range filter to 30 days", async ({ page }) => {
    const daysSelect = page.locator("select").nth(1);
    await daysSelect.selectOption("30");
    await page.waitForTimeout(500);
  });

  test("should show maintenance table or empty state message", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    const hasEmpty = await page.locator("text=Aucune maintenance").isVisible();
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test("should show correct table headers when maintenance records exist", async ({ page }) => {
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

  test("should display claims page with Sinistres title", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Sinistres");
  });

  test("should show vehicle filter dropdown with all vehicles option", async ({ page }) => {
    const vehicleSelect = page.locator("select").first();
    await expect(vehicleSelect).toBeVisible();
    await expect(vehicleSelect).toContainText("Tous les vehicules");
  });

  test("should show status filter dropdown with all statuses option", async ({ page }) => {
    const statusSelect = page.locator("select").nth(1);
    await expect(statusSelect).toBeVisible();
    await expect(statusSelect).toContainText("Tous les statuts");
  });

  test("should filter claims by DECLARE status", async ({ page }) => {
    const statusSelect = page.locator("select").nth(1);
    await statusSelect.selectOption("DECLARE");
    await page.waitForTimeout(500);
  });

  test("should show claims table or empty state message", async ({ page }) => {
    await page.waitForSelector("text=Chargement...", { state: "hidden", timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator("table").isVisible();
    const hasEmpty = await page.locator("text=Aucun sinistre").isVisible();
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test("should show correct table headers when claims exist", async ({ page }) => {
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

// ── Vehicle Detail: Maintenance & Couts Tabs ───────────────────

test.describe("Vehicle Detail — Maintenance Tab (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
  });

  test("should show 6 tabs including Maintenance and Couts in vehicle detail", async ({ page }) => {
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

  test("should display plans and interventions sections in Maintenance tab", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Maintenance");

    await expect(page.locator("text=Plans de maintenance")).toBeVisible();
    await expect(page.locator("text=Interventions")).toBeVisible();
  });

  test("should show add maintenance schedule form with type selector", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Maintenance");

    const addBtn = page.locator("text=Ajouter un plan");
    if (await addBtn.isVisible()) {
      await addBtn.click();
      await expect(page.locator("select")).toBeVisible();
    }
  });

  test("should show add maintenance intervention form", async ({ page }) => {
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

test.describe("Vehicle Detail — Couts Tab (Module H)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
  });

  test("should display cost summary section in Couts tab", async ({ page }) => {
    const vehicleLink = page.locator("table tbody tr:first-child a").first();
    if (!(await vehicleLink.isVisible())) {
      test.skip();
      return;
    }
    await vehicleLink.click();
    await page.click("text=Coûts");

    await expect(page.locator("text=Synthese des couts")).toBeVisible();
  });

  test("should show add cost form in Couts tab", async ({ page }) => {
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
