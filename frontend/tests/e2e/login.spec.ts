import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

test.describe("Login", () => {
  test("should login and redirect to jobs page", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page).toHaveURL(/.*\/jobs/);
    await expect(page.locator("text=Missions")).toBeVisible();
  });

  test("should show error for invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "wrong@test.com");
    await page.fill('input[type="password"]', "wrong");
    await page.click('button[type="submit"]');
    await expect(page.locator("text=incorrect")).toBeVisible();
  });
});
