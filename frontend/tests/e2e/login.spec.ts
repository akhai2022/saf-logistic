import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

/**
 * E2E Scenarios: Authentication (Module A)
 *
 * Covers: Successful login with redirect, invalid credentials error display.
 * The login flow returns JWT + tenant + permissions + dashboard_config
 * which drives the entire frontend (sidebar sections, page access).
 */
test.describe("Login", () => {
  test("should login with valid credentials and redirect to jobs page", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page).toHaveURL(/.*\/jobs/);
    await expect(page.locator("text=Missions")).toBeVisible();
  });

  test("should show error message for invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "wrong@test.com");
    await page.fill('input[type="password"]', "wrong");
    await page.click('button[type="submit"]');
    await expect(page.locator("text=incorrect")).toBeVisible();
  });
});
