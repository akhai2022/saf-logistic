import { Page } from "@playwright/test";

const TENANT_ID = "00000000-0000-0000-0000-000000000001";

/** Login as admin (default demo user). */
export async function loginAsAdmin(page: Page) {
  await page.goto("/login");
  await page.fill('input[type="email"]', "admin@saf.local");
  await page.fill('input[type="password"]', "admin");
  // Tenant ID should be pre-filled
  await page.click('button[type="submit"]');
  // Wait for redirect
  await page.waitForURL("**/jobs");
}

/** Generic login helper for any persona. */
export async function loginAs(
  page: Page,
  email: string,
  password: string,
) {
  await page.goto("/login");
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/jobs");
}

/** Persona login shortcuts. */
export const loginAsDirigeant = (page: Page) =>
  loginAs(page, "dirigeant@saf.local", "dirigeant2026");

export const loginAsExploitant = (page: Page) =>
  loginAs(page, "exploitant@saf.local", "exploit2026");

export const loginAsCompta = (page: Page) =>
  loginAs(page, "compta@saf.local", "compta2026");

export const loginAsRH = (page: Page) =>
  loginAs(page, "rh@saf.local", "rh2026");

export const loginAsFlotte = (page: Page) =>
  loginAs(page, "flotte@saf.local", "flotte2026");

export const loginAsSousTraitant = (page: Page) =>
  loginAs(page, "soustraitant@saf.local", "soustraitant2026");

export const loginAsAuditeur = (page: Page) =>
  loginAs(page, "auditeur@saf.local", "audit2026");
