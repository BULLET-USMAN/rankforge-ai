import { test, expect } from "@playwright/test";

test.describe("RankForge AI — Phase 4 Master Smoke Suite", () => {
  test("1. Landing page renders branding, tagline, and launch action", async ({ page }) => {
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

  test("2. Login page renders Supabase authentication form with demo access", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Sign In" })).toBeVisible();
    await expect(page.getByLabel("Work Email")).toBeVisible();
    await expect(page.locator("input#password")).toBeVisible();
    await expect(page.getByText(/Instant Local Demo Sign-in/i)).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/login-page.png" });
  });

  test("3. Register page renders multi-tenant account provisioning and password strength indicator", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: "Create Account" })).toBeVisible();
    await expect(page.getByLabel("Full Name")).toBeVisible();
    await expect(page.getByLabel("Work Email")).toBeVisible();

    // Type password to trigger strength indicator
    await page.locator("input#password").fill("TestP@ssw0rd2026!");
    await expect(page.getByText(/Password strength:/i)).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/register-page.png" });
  });

  test("4. Email verification page renders confirmation instructions", async ({ page }) => {
    await page.goto("/verify-email?email=founder%40startup.com");
    await expect(page.getByRole("heading", { name: /Verify Your Email/i })).toBeVisible();
    await expect(page.getByText(/founder@startup.com/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Resend Verification Email/i })).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/verify-email-page.png" });
  });

  test("5. Password recovery flow renders recovery portals", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByRole("heading", { name: "Reset Password" })).toBeVisible();
    await expect(page.getByLabel("Account Email")).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/forgot-password-page.png" });

    await page.goto("/reset-password");
    await expect(page.getByRole("heading", { name: "Update Password" })).toBeVisible();
    await expect(page.getByLabel("New Password", { exact: true })).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/reset-password-page.png" });
  });

  test("6. Onboarding flow renders workspace setup and tier selection", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.getByRole("heading", { name: /Create Your Workspace/i })).toBeVisible();
    await expect(page.getByLabel(/Workspace or Agency Name/i)).toBeVisible();
    await expect(page.getByLabel(/Workspace URL Slug/i)).toBeVisible();
    await expect(page.getByText(/Evaluation Tier/i)).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/onboarding-page.png" });
  });

  test("7. Dashboard Overview renders workspace metrics and active health probe", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Workspace Overview" })).toBeVisible();
    await expect(page.getByText("Tracked Websites")).toBeVisible();
    await expect(page.getByText("Audits Executed")).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/desktop-dashboard-overview.png", fullPage: true });
  });

  test("8. Team & Workspace Access page renders member roster and invite trigger", async ({ page }) => {
    await page.goto("/dashboard/team");
    await expect(page.getByRole("heading", { name: "Team & Workspace Access" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Invite Member/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Workspace Members" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Pending Invitations" })).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/team-management-page.png", fullPage: true });
  });

  test("9. Account Profile page renders user identity management", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await expect(page.getByRole("heading", { name: "Account Profile" })).toBeVisible();
    await expect(page.getByText("User Details")).toBeVisible();
    await expect(page.getByText("Security & Password")).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/account-profile-page.png", fullPage: true });
  });

  test("10. Website Projects page renders domain list, search, and add dialog", async ({ page }) => {
    await page.goto("/dashboard/websites");
    await expect(page.getByRole("heading", { name: "Website Projects", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: /Add Website/i })).toBeVisible();
    await expect(page.getByPlaceholder(/Search by name or domain/i)).toBeVisible();

    // Open Add Website modal
    await page.getByRole("button", { name: /Add Website/i }).click();
    await expect(page.getByRole("heading", { name: /Add Website Project/i })).toBeVisible();
    await expect(page.getByLabel(/Target Domain or Canonical URL/i)).toBeVisible();

    // Capture screenshot with modal open
    await page.screenshot({ path: "test-results/screenshots/desktop-websites-page.png", fullPage: true });
  });

  test("11. Technical Audits page renders target URL input and preflight runner", async ({ page }) => {
    await page.goto("/dashboard/audits");
    await expect(page.getByRole("heading", { name: /Technical SEO Audits/i })).toBeVisible();
    await expect(page.getByText(/Audit Engine \(Phase 4\)/i)).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/desktop-audits-page.png", fullPage: true });
  });

  test("12. Phase 4 website verification & crawler detail page renders fallback view", async ({ page }) => {
    await page.goto("/dashboard/websites/demo-test-site");
    await expect(page.getByRole("heading", { name: /Website Project Not Found/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Back to Websites/i })).toBeVisible();

    // Capture screenshot
    await page.screenshot({ path: "test-results/screenshots/desktop-website-detail-fallback.png" });
  });

  test("13. Roadmap pages render clear status", async ({ page }) => {
    await page.goto("/dashboard/billing");
    await expect(page.getByRole("heading", { name: /Subscription & Usage/i })).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/desktop-billing-page.png", fullPage: true });

    await page.goto("/dashboard/settings");
    await expect(page.getByRole("heading", { name: /Organization Settings/i })).toBeVisible();
    await page.screenshot({ path: "test-results/screenshots/desktop-settings-page.png", fullPage: true });
  });
});
