import { test, expect } from "@playwright/test";

test.describe("RankForge AI Smoke Tests", () => {
  test("1. Landing page renders branding, tagline, and primary actions", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/RankForge AI/i);

    // Verify tagline & heading
    await expect(page.getByRole("heading", { name: /Search intelligence/i })).toBeVisible();
    await expect(page.getByText(/Engineered for growth/i).first()).toBeVisible();

    // Verify primary action
    const cta = page.getByRole("link", { name: /Launch Overview Dashboard/i });
    await expect(cta).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/landing-page.png", fullPage: true });
  });

  test("2. Login page renders validated interface and dev mode notice", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText(/Sign In to Workspace/i)).toBeVisible();
    await expect(page.getByText(/Phase 1 Architecture Notice/i)).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/login-page.png" });
  });

  test("3. Register page renders tenant workspace creation form", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByText(/Create Workspace/i)).toBeVisible();
    await expect(page.getByText(/Multi-Tenant Architecture/i)).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/register-page.png" });
  });

  test("4. Dashboard Overview page renders metric cards and platform status", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText(/Workspace Overview/i)).toBeVisible();
    await expect(page.getByText(/Tracked Websites/i)).toBeVisible();
    await expect(page.getByText(/Audits Executed/i)).toBeVisible();
    await expect(page.getByText(/Platform Readiness/i)).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/desktop-dashboard-overview.png", fullPage: true });
  });

  test("5. Websites page renders project list and verification protocols", async ({ page }) => {
    await page.goto("/dashboard/websites");
    await expect(page.getByRole("heading", { name: /Website Projects/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Add Website Project/i })).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/desktop-websites-page.png", fullPage: true });
  });

  test("6. Audits page renders target URL input and preflight runner", async ({ page }) => {
    await page.goto("/dashboard/audits");
    await expect(page.getByText(/Technical SEO Audits/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Preflight Audit/i })).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/desktop-audits-page.png", fullPage: true });
  });

  test("7. Phase 2 specification pages render differentiated coming soon states", async ({ page }) => {
    // Keywords
    await page.goto("/dashboard/keywords");
    await expect(page.getByText(/Keyword Intelligence & Search Analytics/i)).toBeVisible();
    await expect(page.getByText(/Phase 2 Release/i)).toBeVisible();

    // Billing
    await page.goto("/dashboard/billing");
    await expect(page.getByText(/Subscription & Usage/i)).toBeVisible();
    await expect(page.getByText(/Billing Environment Status/i)).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/desktop-billing-page.png", fullPage: true });

    // Settings
    await page.goto("/dashboard/settings");
    await expect(page.getByText(/Organization Settings/i)).toBeVisible();
    await expect(page.getByText(/Crawler Engine Security Policy/i)).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/desktop-settings-page.png", fullPage: true });
  });
});
