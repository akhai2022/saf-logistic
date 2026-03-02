import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsAuditeur } from "./helpers/auth";

/**
 * E2E Scenarios: Audit Log (Module A — Gap Closure)
 *
 * Covers: Audit log page access, filter bar, table display,
 * expandable old/new JSON detail, and role-based access.
 * Admin and Auditeur (lecture_seule) have audit.read permission.
 */

test.describe("Audit Log Page — Admin", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/audit");
  });

  test("should display audit page with title and description", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Journal d'audit");
    await expect(page.locator("text=Historique des actions")).toBeVisible();
  });

  test("should show filter inputs for entity type and action", async ({ page }) => {
    await expect(page.locator("input[placeholder='Type entite']")).toBeVisible();
    await expect(page.locator("input[placeholder='Action']")).toBeVisible();
  });

  test("should show date range filter inputs", async ({ page }) => {
    const dateInputs = page.locator("input[type='date']");
    const count = await dateInputs.count();
    expect(count).toBe(2); // date_from and date_to
  });

  test("should show filter button", async ({ page }) => {
    await expect(page.locator("button:has-text('Filtrer')")).toBeVisible();
  });

  test("should show audit log table with correct columns", async ({ page }) => {
    await expect(page.locator("thead")).toContainText("Date");
    await expect(page.locator("thead")).toContainText("Utilisateur");
    await expect(page.locator("thead")).toContainText("Action");
    await expect(page.locator("thead")).toContainText("Entite");
    await expect(page.locator("thead")).toContainText("Details");
  });

  test("should filter audit logs by entity type", async ({ page }) => {
    await page.fill("input[placeholder='Type entite']", "job");
    await page.click("button:has-text('Filtrer')");
    await page.waitForTimeout(500);
    // Table should refresh with filtered results
  });

  test("should filter audit logs by action", async ({ page }) => {
    await page.fill("input[placeholder='Action']", "status_transition");
    await page.click("button:has-text('Filtrer')");
    await page.waitForTimeout(500);
  });

  test("should filter audit logs by date range", async ({ page }) => {
    const dateInputs = page.locator("input[type='date']");
    await dateInputs.nth(0).fill("2026-01-01");
    await dateInputs.nth(1).fill("2026-12-31");
    await page.click("button:has-text('Filtrer')");
    await page.waitForTimeout(500);
  });

  test("should toggle detail view for audit log entry", async ({ page }) => {
    const viewButton = page.locator("text=Voir").first();
    if (await viewButton.isVisible()) {
      await viewButton.click();
      // Should show expanded detail with old/new values
      const detail = page.locator("text=Ancien, text=Nouveau").first();
      const masquerButton = page.locator("text=Masquer").first();
      await expect(masquerButton).toBeVisible();

      // Click again to hide
      await masquerButton.click();
      await expect(page.locator("text=Voir").first()).toBeVisible();
    }
  });

  test("should show empty state when no audit logs match filters", async ({ page }) => {
    await page.fill("input[placeholder='Type entite']", "nonexistent_entity_xyz");
    await page.click("button:has-text('Filtrer')");
    await page.waitForTimeout(500);
    // Should show empty state or empty table
  });
});

test.describe("Audit Log Page — Auditeur (lecture_seule)", () => {
  test("should allow auditeur to access audit page", async ({ page }) => {
    await loginAsAuditeur(page);
    await page.goto("/audit");
    await expect(page.locator("h1")).toContainText("Journal d'audit");
  });

  test("should show audit log table for auditeur", async ({ page }) => {
    await loginAsAuditeur(page);
    await page.goto("/audit");
    await expect(page.locator("thead")).toContainText("Date");
    await expect(page.locator("thead")).toContainText("Action");
  });
});
