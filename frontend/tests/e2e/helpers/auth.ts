import { Page } from "@playwright/test";

const TENANT_ID = "00000000-0000-0000-0000-000000000001";

export async function loginAsAdmin(page: Page) {
  await page.goto("/login");
  await page.fill('input[type="email"]', "admin@saf.local");
  await page.fill('input[type="password"]', "admin");
  // Tenant ID should be pre-filled
  await page.click('button[type="submit"]');
  // Wait for redirect
  await page.waitForURL("**/jobs");
}
