import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers/auth";

test.describe("Jobs", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("should display jobs list", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Missions");
  });

  test("should create a new job", async ({ page }) => {
    await page.click("text=Nouvelle mission");
    await page.fill('input[placeholder=""]', "TEST-E2E");
    await page.click("text=Créer la mission");
    await expect(page.locator("text=TEST-E2E")).toBeVisible();
  });
});
