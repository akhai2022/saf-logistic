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
 * E2E Scenarios: Persona-based Access & Parametrage
 *
 * Verifies each persona can log in and sees role-appropriate sidebar sections.
 * Tests the parametrage flow: login → dashboard_config → filtered Nav.
 */

test.describe("Persona: Dirigeant (admin)", () => {
  test("should login and see all sidebar sections", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/jobs");

    // Admin sees all sections
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
    await expect(page.locator("nav >> text=Clients")).toBeVisible();
    await expect(page.locator("nav >> text=Factures")).toBeVisible();
    await expect(page.locator("nav >> text=Flotte").first()).toBeVisible();
    await expect(page.locator("nav >> text=Pilotage").first()).toBeVisible();
  });

  test("should access fleet dashboard", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/fleet");
    await expect(page.locator("h1")).toContainText("Flotte");
  });

  test("should access reports dashboard", async ({ page }) => {
    await loginAsDirigeant(page);
    await page.goto("/reports");
    await expect(page.locator("h1")).toContainText("Pilotage");
  });
});

test.describe("Persona: Exploitant", () => {
  test("should login successfully", async ({ page }) => {
    await loginAsExploitant(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see exploitation section in sidebar", async ({ page }) => {
    await loginAsExploitant(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
    await expect(page.locator("nav >> text=Litiges")).toBeVisible();
  });

  test("should access jobs page", async ({ page }) => {
    await loginAsExploitant(page);
    await page.goto("/jobs");
    await expect(page.locator("h1")).toContainText("Missions");
  });
});

test.describe("Persona: Comptable", () => {
  test("should login successfully", async ({ page }) => {
    await loginAsCompta(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see finance section in sidebar", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Factures")).toBeVisible();
  });

  test("should access reports page", async ({ page }) => {
    await loginAsCompta(page);
    await page.goto("/reports");
    await expect(page.locator("h1")).toContainText("Pilotage");
  });
});

test.describe("Persona: RH / Paie", () => {
  test("should login successfully", async ({ page }) => {
    await loginAsRH(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should access drivers page", async ({ page }) => {
    await loginAsRH(page);
    await page.goto("/drivers");
    await expect(page.locator("h1")).toContainText("Conducteurs");
  });
});

test.describe("Persona: Flotte", () => {
  test("should login successfully", async ({ page }) => {
    await loginAsFlotte(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see flotte section in sidebar", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Flotte").first()).toBeVisible();
  });

  test("should access fleet dashboard", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/fleet");
    await expect(page.locator("h1")).toContainText("Flotte");
  });

  test("should access maintenance page", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/fleet/maintenance");
    await expect(page.locator("h1")).toContainText("Maintenance");
  });

  test("should access claims page", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/fleet/claims");
    await expect(page.locator("h1")).toContainText("Sinistres");
  });

  test("should access vehicles page", async ({ page }) => {
    await loginAsFlotte(page);
    await page.goto("/vehicles");
    await expect(page.locator("h1")).toContainText("Véhicules");
  });
});

test.describe("Persona: Sous-traitant", () => {
  test("should login successfully", async ({ page }) => {
    await loginAsSousTraitant(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see limited sidebar (exploitation only)", async ({ page }) => {
    await loginAsSousTraitant(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
  });
});

test.describe("Persona: Auditeur (lecture seule)", () => {
  test("should login successfully", async ({ page }) => {
    await loginAsAuditeur(page);
    await expect(page).toHaveURL(/\/jobs/);
  });

  test("should see all sidebar sections (read-only)", async ({ page }) => {
    await loginAsAuditeur(page);
    await page.goto("/jobs");
    await expect(page.locator("nav >> text=Missions")).toBeVisible();
    await expect(page.locator("nav >> text=Clients")).toBeVisible();
  });

  test("should access reports page", async ({ page }) => {
    await loginAsAuditeur(page);
    await page.goto("/reports");
    await expect(page.locator("h1")).toContainText("Pilotage");
  });
});

test.describe("Login validation", () => {
  test("should reject wrong password", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "admin@saf.local");
    await page.fill('input[type="password"]', "wrong_password");
    await page.click('button[type="submit"]');
    await expect(page.locator("text=incorrect")).toBeVisible();
  });

  test("should reject non-existent user", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "nonexistent@saf.local");
    await page.fill('input[type="password"]', "anypassword");
    await page.click('button[type="submit"]');
    await expect(page.locator("text=incorrect")).toBeVisible();
  });
});
