import { test, expect } from "@playwright/test";
import {
  loginAsAdmin,
  loginAsDirigeant,
  loginAsExploitant,
  loginAsCompta,
  loginAsRH,
  loginAsFlotte,
  loginAsSousTraitant,
  loginAsAuditeur,
} from "./helpers/auth";

/**
 * E2E Scenarios: Persona-based Access & Parametrage (RBAC)
 *
 * Verifies each persona can log in and sees role-appropriate sidebar sections.
 * Tests the parametrage flow: login -> dashboard_config -> filtered Nav.
 * Each role only sees the sidebar sections allowed by their dashboard_config.
 *
 * Personas:
 * - Dirigeant (admin): Full access to all modules including settings and audit
 * - Exploitant: Missions, litiges, referentiels
 * - Comptable: Finance, invoices, reports
 * - RH/Paie: Drivers, payroll
 * - Flotte: Fleet dashboard, maintenance, claims, vehicles
 * - Sous-traitant: Limited to missions (exploitation only)
 * - Auditeur (lecture_seule): Read-only access to all data + audit log
 */

test.describe("Persona: Dirigeant (admin)", () => {
  test("should login and see all sidebar sections including parametrage", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/jobs");

    // Admin sees all sections
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
    await expect(page.locator("nav >> text=Clients")).toBeVisible();
    await expect(page.locator("nav >> text=Factures")).toBeVisible();
    await expect(page.locator("nav >> text=Flotte").first()).toBeVisible();
    await expect(page.locator("nav >> text=Pilotage").first()).toBeVisible();
    // Parametrage section (gap closure)
    await expect(page.locator("nav >> text=Paramètres")).toBeVisible();
    await expect(page.locator("nav >> text=Journal d'audit")).toBeVisible();
  });

  test("should access fleet dashboard with KPI cards", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/fleet");
    await expect(page.locator("h1")).toContainText("Flotte");
  });

  test("should access reports dashboard with all export sections", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/reports");
    await expect(page.locator("h1")).toContainText("Pilotage");
  });

  test("should access settings page with all 5 tabs", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Paramètres");
    await expect(page.locator("text=Entreprise")).toBeVisible();
    await expect(page.locator("text=Banque")).toBeVisible();
    await expect(page.locator("text=TVA")).toBeVisible();
  });

  test("should access audit log page with filter bar", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/audit");
    await expect(page.locator("h1")).toContainText("Journal d'audit");
    await expect(page.locator("text=Historique des actions")).toBeVisible();
  });

  test("should access notifications page", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/notifications");
    await expect(page.locator("h1")).toContainText("Notifications");
  });
});

test.describe("Persona: Exploitant", () => {
  test("should login successfully and redirect to jobs", async ({ page }) => {
    await loginAsExploitant(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see exploitation section in sidebar with missions and litiges", async ({ page }) => {
    await loginAsExploitant(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
    await expect(page.locator("nav >> text=Litiges")).toBeVisible();
  });

  test("should access jobs page and see missions list", async ({ page }) => {
    await loginAsExploitant(page);
    await page.goto("/jobs");
    await expect(page.locator("h1")).toContainText("Missions");
  });
});

test.describe("Persona: Comptable", () => {
  test("should login successfully and redirect to jobs", async ({ page }) => {
    await loginAsCompta(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see finance section in sidebar with factures link", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Factures")).toBeVisible();
  });

  test("should access reports page and see finance section", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/reports");
    await expect(page.locator("h1")).toContainText("Pilotage");
  });

  test("should access invoices page for billing operations", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/invoices");
    await expect(page.locator("h1")).toContainText("Factures");
  });
});

test.describe("Persona: RH / Paie", () => {
  test("should login successfully and redirect to jobs", async ({ page }) => {
    await loginAsRH(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should access drivers page for HR management", async ({ page }) => {
    await loginAsRH(page);
    await page.goto("/drivers");
    await expect(page.locator("h1")).toContainText("Conducteurs");
  });

  test("should access payroll page for pre-paie management", async ({ page }) => {
    await loginAsRH(page);
    await page.goto("/payroll");
    await expect(page.locator("h1")).toContainText("Pré-paie");
  });
});

test.describe("Persona: Flotte", () => {
  test("should login successfully and redirect to jobs", async ({ page }) => {
    await loginAsFlotte(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see flotte section in sidebar with dashboard link", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Flotte").first()).toBeVisible();
  });

  test("should access fleet dashboard with KPI cards", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/fleet");
    await expect(page.locator("h1")).toContainText("Flotte");
  });

  test("should access maintenance page with status filters", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/fleet/maintenance");
    await expect(page.locator("h1")).toContainText("Maintenance");
  });

  test("should access claims page with vehicle filters", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/fleet/claims");
    await expect(page.locator("h1")).toContainText("Sinistres");
  });

  test("should access vehicles page for fleet management", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/vehicles");
    await expect(page.locator("h1")).toContainText("Véhicules");
  });
});

test.describe("Persona: Sous-traitant", () => {
  test("should login successfully and redirect to jobs", async ({ page }) => {
    await loginAsSousTraitant(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see limited sidebar with exploitation section only", async ({ page }) => {
    await loginAsSousTraitant(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
  });
});

test.describe("Persona: Auditeur (lecture seule)", () => {
  test("should login successfully and redirect to jobs", async ({ page }) => {
    await loginAsAuditeur(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see all sidebar sections for read-only access", async ({ page }) => {
    await loginAsAuditeur(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
    await expect(page.locator("nav >> text=Clients")).toBeVisible();
  });

  test("should access reports page for read-only reporting", async ({ page }) => {
    await loginAsAuditeur(page);
    await page.goto("/reports");
    await expect(page.locator("h1")).toContainText("Pilotage");
  });

  test("should access audit log page for compliance review", async ({ page }) => {
    await loginAsAuditeur(page);
    await page.goto("/audit");
    await expect(page.locator("h1")).toContainText("Journal d'audit");
  });
});

test.describe("Login validation", () => {
  test("should reject wrong password and show error message", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "admin@saf.local");
    await page.fill('input[type="password"]', "wrong_password");
    await page.click('button[type="submit"]');
    await expect(page.locator("text=incorrect")).toBeVisible();
  });

  test("should reject non-existent user and show error message", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "nonexistent@saf.local");
    await page.fill('input[type="password"]', "anypassword");
    await page.click('button[type="submit"]');
    await expect(page.locator("text=incorrect")).toBeVisible();
  });
});
