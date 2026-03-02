import { test, expect, Page } from "@playwright/test";
import { loginAsAdmin, loginAs } from "./helpers/auth";

/**
 * Demo Screenshots Capture Script
 *
 * Captures screenshots for the SAF Logistic demo walkthrough.
 * Each test corresponds to a scene in the DEMO_WALKTHROUGH.md.
 *
 * Run with: npx playwright test capture-demo-screenshots --project=chromium
 * Output: demo-screenshots/ directory
 */

import path from "path";
const SCREENSHOT_DIR = path.resolve(__dirname, "../../../demo-screenshots");

async function waitForLoad(page: Page) {
  await page
    .waitForSelector("text=Chargement...", { state: "hidden", timeout: 15000 })
    .catch(() => {});
  await page.waitForTimeout(1200);
}

async function shot(page: Page, name: string) {
  await page.screenshot({
    path: `${SCREENSHOT_DIR}/${name}.png`,
    fullPage: true,
  });
}

async function shotViewport(page: Page, name: string) {
  await page.screenshot({
    path: `${SCREENSHOT_DIR}/${name}.png`,
    fullPage: false,
  });
}

// ── SCENE 1: Login Page ──────────────────────────────────────

test.describe("Demo Screenshots — Connexion", () => {
  test("Scene 01a — Login page", async ({ page }) => {
    await page.goto("/login");
    await page.waitForTimeout(500);
    await shot(page, "01a-login-page");
  });

  test("Scene 01b — Login filled", async ({ page }) => {
    await page.goto("/login");
    await page.waitForTimeout(500);
    await page.fill('input[type="email"]', "admin@saf.local");
    await page.fill('input[type="password"]', "admin");
    await shot(page, "01b-login-filled");
  });

  test("Scene 01c — After login — Missions page", async ({ page }) => {
    await loginAsAdmin(page);
    await waitForLoad(page);
    await shot(page, "01c-missions-after-login");
  });
});

// ── SCENE 2: Sidebar & Navigation ──────────────────────────

test.describe("Demo Screenshots — Sidebar", () => {
  test("Scene 02a — Sidebar navigation", async ({ page }) => {
    await loginAsAdmin(page);
    await waitForLoad(page);
    await shotViewport(page, "02a-sidebar-navigation");
  });
});

// ── SCENE 3: Clients ──────────────────────────────────────

test.describe("Demo Screenshots — Clients", () => {
  test("Scene 03a — Clients list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/customers");
    await waitForLoad(page);
    await shot(page, "03a-clients-list");
  });

  test("Scene 03b — New client form", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/customers");
    await waitForLoad(page);
    const newBtn = page.locator("button:has-text('Nouveau client'), a:has-text('Nouveau client')");
    if (await newBtn.first().isVisible().catch(() => false)) {
      await newBtn.first().click();
      await page.waitForTimeout(500);
    }
    await shot(page, "03b-new-client-form");
  });

  test("Scene 03c — Client detail", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/customers");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a, table tbody tr:first-child td").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
    }
    await shot(page, "03c-client-detail");
  });
});

// ── SCENE 4: Conducteurs & Vehicules ──────────────────────

test.describe("Demo Screenshots — Conducteurs", () => {
  test("Scene 04a — Conducteurs list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/drivers");
    await waitForLoad(page);
    await shot(page, "04a-conducteurs-list");
  });

  test("Scene 04b — Conducteur detail", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/drivers");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a, table tbody tr:first-child td").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
    }
    await shot(page, "04b-conducteur-detail");
  });
});

test.describe("Demo Screenshots — Vehicules", () => {
  test("Scene 04c — Vehicules list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
    await waitForLoad(page);
    await shot(page, "04c-vehicules-list");
  });

  test("Scene 04d — Vehicule detail", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/vehicles");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
    }
    await shot(page, "04d-vehicule-detail");
  });
});

// ── SCENE 5: Conformite ───────────────────────────────────

test.describe("Demo Screenshots — Conformite", () => {
  test("Scene 05a — Conformite dashboard", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance");
    await waitForLoad(page);
    await shot(page, "05a-conformite-dashboard");
  });

  test("Scene 05b — Conformite alerts", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/compliance/alerts");
    await waitForLoad(page);
    await shot(page, "05b-conformite-alerts");
  });
});

// ── SCENE 6: Missions ─────────────────────────────────────

test.describe("Demo Screenshots — Missions", () => {
  test("Scene 06a — Missions list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/jobs");
    await waitForLoad(page);
    await shot(page, "06a-missions-list");
  });

  test("Scene 06b — New mission form", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/jobs");
    await waitForLoad(page);
    const newBtn = page.locator("button:has-text('Nouvelle mission'), a:has-text('Nouvelle mission')");
    if (await newBtn.first().isVisible().catch(() => false)) {
      await newBtn.first().click();
      await page.waitForTimeout(500);
    }
    await shot(page, "06b-new-mission-form");
  });

  test("Scene 06c — Mission detail", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/jobs");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
    }
    await shot(page, "06c-mission-detail");
  });

  test("Scene 06d — Mission detail Livraisons tab", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/jobs");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
      const livraisonsTab = page.locator("button:has-text('Livraisons'), [role='tab']:has-text('Livraisons')").first();
      if (await livraisonsTab.isVisible().catch(() => false)) await livraisonsTab.click();
      await page.waitForTimeout(500);
    }
    await shot(page, "06d-mission-livraisons");
  });

  test("Scene 06e — Mission detail Marchandises tab", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/jobs");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
      const tab = page.locator("button:has-text('Marchandises'), [role='tab']:has-text('Marchandises')").first();
      if (await tab.isVisible().catch(() => false)) await tab.click();
      await page.waitForTimeout(500);
    }
    await shot(page, "06e-mission-marchandises");
  });

  test("Scene 06f — Mission detail POD tab", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/jobs");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
      const tab = page.locator("button:has-text('POD'), [role='tab']:has-text('POD')").first();
      if (await tab.isVisible().catch(() => false)) await tab.click();
      await page.waitForTimeout(500);
    }
    await shot(page, "06f-mission-pod");
  });

  test("Scene 06g — Mission detail Litiges tab", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/jobs");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
      const tab = page.locator("button:has-text('Litiges'), [role='tab']:has-text('Litiges')").first();
      if (await tab.isVisible().catch(() => false)) await tab.click();
      await page.waitForTimeout(500);
    }
    await shot(page, "06g-mission-litiges");
  });
});

// ── SCENE 7: Litiges ──────────────────────────────────────

test.describe("Demo Screenshots — Litiges", () => {
  test("Scene 07a — Litiges list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/disputes");
    await waitForLoad(page);
    await shot(page, "07a-litiges-list");
  });

  test("Scene 07b — Litiges status tabs", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/disputes");
    await waitForLoad(page);
    const tab = page.locator("text=Ouverts");
    if (await tab.isVisible().catch(() => false)) await tab.click();
    await page.waitForTimeout(500);
    await shot(page, "07b-litiges-ouverts");
  });
});

// ── SCENE 8: Fleet Dashboard ──────────────────────────────

test.describe("Demo Screenshots — Fleet Dashboard", () => {
  test("Scene 08a — Fleet dashboard", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet");
    await waitForLoad(page);
    await shot(page, "08a-fleet-dashboard");
  });
});

// ── SCENE 9: Maintenance ──────────────────────────────────

test.describe("Demo Screenshots — Maintenance", () => {
  test("Scene 09a — Maintenance list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/maintenance");
    await waitForLoad(page);
    await shot(page, "09a-maintenance-list");
  });

  test("Scene 09b — New maintenance form", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/maintenance");
    await waitForLoad(page);
    const btn = page.locator("text=Nouvelle intervention").first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(800);
    }
    await shot(page, "09b-new-maintenance-form");
  });
});

// ── SCENE 10: Sinistres ───────────────────────────────────

test.describe("Demo Screenshots — Sinistres", () => {
  test("Scene 10a — Sinistres list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/claims");
    await waitForLoad(page);
    await shot(page, "10a-sinistres-list");
  });

  test("Scene 10b — Declarer sinistre form", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/fleet/claims");
    await waitForLoad(page);
    const btn = page.locator("text=Declarer un sinistre").first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(800);
    }
    await shot(page, "10b-declarer-sinistre-form");
  });
});

// ── SCENE 11: Facturation ─────────────────────────────────

test.describe("Demo Screenshots — Facturation", () => {
  test("Scene 11a — Tarifs list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/pricing");
    await waitForLoad(page);
    await shot(page, "11a-tarifs-list");
  });

  test("Scene 11b — New tarif form", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/pricing");
    await waitForLoad(page);
    const btn = page.locator("text=Nouveau tarif").first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(500);
    }
    await shot(page, "11b-new-tarif-form");
  });

  test("Scene 11c — Factures list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/invoices");
    await waitForLoad(page);
    await shot(page, "11c-factures-list");
  });

  test("Scene 11d — Facture detail", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/invoices");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
    }
    await shot(page, "11d-facture-detail");
  });

  test("Scene 11e — Factures fournisseurs", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/supplier-invoices");
    await waitForLoad(page);
    await shot(page, "11e-factures-fournisseurs");
  });
});

// ── SCENE 12: OCR ─────────────────────────────────────────

test.describe("Demo Screenshots — OCR", () => {
  test("Scene 12a — OCR page", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/ocr");
    await waitForLoad(page);
    await shot(page, "12a-ocr-page");
  });
});

// ── SCENE 13: Paie ────────────────────────────────────────

test.describe("Demo Screenshots — Paie", () => {
  test("Scene 13a — Paie page", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/payroll");
    await waitForLoad(page);
    await shot(page, "13a-paie-page");
  });
});

// ── SCENE 14: Taches ──────────────────────────────────────

test.describe("Demo Screenshots — Taches", () => {
  test("Scene 14a — Taches page", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/tasks");
    await waitForLoad(page);
    await shot(page, "14a-taches-page");
  });
});

// ── SCENE 15: Reporting / KPI ─────────────────────────────

test.describe("Demo Screenshots — Reporting", () => {
  test("Scene 15a — Reporting dashboard", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports");
    await waitForLoad(page);
    await shot(page, "15a-reporting-dashboard");
  });
});

// ── SCENE 16: Parametrage ─────────────────────────────────

test.describe("Demo Screenshots — Parametrage", () => {
  test("Scene 16a — Settings page", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await waitForLoad(page);
    await shot(page, "16a-settings-entreprise");
  });

  test("Scene 16b — Settings banque tab", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await waitForLoad(page);
    const tab = page.locator("text=Banque").first();
    if (await tab.isVisible().catch(() => false)) {
      await tab.click();
      await page.waitForTimeout(500);
    }
    await shot(page, "16b-settings-banque");
  });

  test("Scene 16c — Settings TVA tab", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/settings");
    await waitForLoad(page);
    const tab = page.locator("text=TVA").first();
    if (await tab.isVisible().catch(() => false)) {
      await tab.click();
      await page.waitForTimeout(500);
    }
    await shot(page, "16c-settings-tva");
  });

  test("Scene 16d — Audit log", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/audit");
    await waitForLoad(page);
    await shot(page, "16d-audit-log");
  });
});

// ── SCENE 17: Notifications ───────────────────────────────

test.describe("Demo Screenshots — Notifications", () => {
  test("Scene 17a — Notifications page", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/notifications");
    await waitForLoad(page);
    await shot(page, "17a-notifications-page");
  });
});

// ── SCENE 18: Multi-roles ─────────────────────────────────

test.describe("Demo Screenshots — Multi-roles", () => {
  test("Scene 18a — Exploitant sidebar", async ({ page }) => {
    await loginAs(page, "exploitant@saf.local", "exploit2026");
    await waitForLoad(page);
    await shotViewport(page, "18a-exploitant-sidebar");
  });

  test("Scene 18b — Compta sidebar", async ({ page }) => {
    await loginAs(page, "compta@saf.local", "compta2026");
    await waitForLoad(page);
    await shotViewport(page, "18b-compta-sidebar");
  });

  test("Scene 18c — Flotte sidebar", async ({ page }) => {
    await loginAs(page, "flotte@saf.local", "flotte2026");
    await waitForLoad(page);
    await shotViewport(page, "18c-flotte-sidebar");
  });

  test("Scene 18d — Auditeur sidebar", async ({ page }) => {
    await loginAs(page, "auditeur@saf.local", "audit2026");
    await waitForLoad(page);
    await shotViewport(page, "18d-auditeur-sidebar");
  });
});

// ── SCENE 19: Onboarding / Configuration ──────────────────

test.describe("Demo Screenshots — Onboarding", () => {
  test("Scene 19a — Onboarding page", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/onboarding");
    await waitForLoad(page);
    await shot(page, "19a-onboarding-page");
  });
});

// ── BONUS: Sous-traitants ─────────────────────────────────

test.describe("Demo Screenshots — Sous-traitants", () => {
  test("Scene B1 — Sous-traitants list", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/subcontractors");
    await waitForLoad(page);
    await shot(page, "B1-soustraitants-list");
  });

  test("Scene B2 — Sous-traitant detail", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/subcontractors");
    await waitForLoad(page);
    const link = page.locator("table tbody tr:first-child a").first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await waitForLoad(page);
    }
    await shot(page, "B2-soustraitant-detail");
  });
});
