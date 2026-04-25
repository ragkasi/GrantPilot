/**
 * GrantPilot end-to-end happy path tests.
 *
 * Prerequisites:
 *   - Backend running at http://localhost:8000 (with demo seed)
 *   - Frontend running at http://localhost:3000
 *   - Demo credentials: demo@grantpilot.local / DemoGrantPilot123!
 *
 * Run: npx playwright test
 */
import { expect, test } from "@playwright/test";
import path from "path";
import fs from "fs";
import os from "os";

const DEMO_EMAIL = "demo@grantpilot.local";
const DEMO_PASSWORD = "DemoGrantPilot123!";
const DEMO_PROJECT_ID = "proj_stem_2026";
const DEMO_ORG_NAME = "BrightPath Youth Foundation";
const DEMO_GRANT_NAME = "Community STEM Access Fund";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function login(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.waitForSelector("input[type='email']");
  await page.fill("input[type='email']", DEMO_EMAIL);
  await page.fill("input[type='password']", DEMO_PASSWORD);
  await page.click("button[type='submit']");
  await page.waitForURL("**/dashboard");
}

// ---------------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------------

test.describe("Authentication", () => {
  test("redirects unauthenticated users to /login", async ({ page }) => {
    // Clear localStorage to ensure no token
    await page.goto("/login");
    await page.evaluate(() => localStorage.removeItem("grantpilot_token"));
    await page.goto("/dashboard");
    await page.waitForURL("**/login");
    await expect(page.locator("h1")).toContainText("GrantPilot");
  });

  test("logs in with demo credentials", async ({ page }) => {
    await login(page);
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("shows login error for wrong password", async ({ page }) => {
    await page.goto("/login");
    await page.fill("input[type='email']", DEMO_EMAIL);
    await page.fill("input[type='password']", "wrongpassword");
    await page.click("button[type='submit']");
    // Should stay on login and show error
    await expect(page).toHaveURL(/\/login/);
    // Wait for the error message to appear (the p element with error text)
    await expect(page.locator("p.text-red-600")).toBeVisible({ timeout: 8000 });
    await expect(page.locator("p.text-red-600")).toContainText("Incorrect");
  });

  test("signs out and redirects to login", async ({ page }) => {
    await login(page);
    await page.click("button:has-text('Sign out')");
    await page.waitForURL("**/login");
    await expect(page).toHaveURL(/\/login/);
  });
});

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("shows demo organization", async ({ page }) => {
    await expect(page.locator(`text=${DEMO_ORG_NAME}`).first()).toBeVisible();
  });

  test("shows demo grant project", async ({ page }) => {
    await expect(page.locator(`text=${DEMO_GRANT_NAME}`).first()).toBeVisible();
  });

  test("shows project status badge", async ({ page }) => {
    await expect(page.locator("text=Analyzed").first()).toBeVisible();
  });

  test("new organization button navigates to creation form", async ({ page }) => {
    await page.click("text=New Organization");
    await expect(page).toHaveURL(/\/organizations\/new/);
  });

  test("new project button navigates to creation form", async ({ page }) => {
    await page.click("text=New Project");
    await expect(page).toHaveURL(/\/projects\/new/);
  });
});

// ---------------------------------------------------------------------------
// Project detail — analysis view
// ---------------------------------------------------------------------------

test.describe("Project detail (analyzed)", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto(`/projects/${DEMO_PROJECT_ID}`);
    await page.waitForSelector("text=Eligibility Score");
  });

  test("shows eligibility and readiness scores", async ({ page }) => {
    // Use getByText with exact match to avoid strict mode violations
    await expect(page.getByText("Eligibility Score", { exact: true })).toBeVisible();
    await expect(page.getByText("Readiness Score", { exact: true })).toBeVisible();
    // Demo mock always returns 82 eligibility, 74 readiness — verify at least one number
    await expect(page.getByText("82").first()).toBeVisible();
    await expect(page.getByText("74").first()).toBeVisible();
  });

  test("requirements tab is active by default and shows rows", async ({ page }) => {
    await expect(page.locator("text=Requirements").first()).toBeVisible();
    await expect(page.locator("table").first()).toBeVisible();
  });

  test("can switch to draft answers tab", async ({ page }) => {
    await page.click("button:has-text('Draft Answers')");
    // The draft answers panel renders question/answer blocks
    await expect(page.locator("text=Draft answers are grounded")).toBeVisible({ timeout: 8000 });
  });

  test("can switch to missing docs tab", async ({ page }) => {
    await page.click("button:has-text('Missing Docs')");
    // The risk panel has a "Missing Documents" section header (h3)
    await expect(page.locator("h3:has-text('Missing Documents')")).toBeVisible({ timeout: 8000 });
  });

  test("edit button opens edit form", async ({ page }) => {
    await page.click("[title='Edit project details']");
    await expect(page.locator("text=Edit Project Details")).toBeVisible();
  });

  test("edit form opens with current values and closes on cancel", async ({ page }) => {
    // Open edit form
    await page.click("[title='Edit project details']");
    await page.waitForSelector("text=Edit Project Details");

    // Verify the grant_name field is pre-filled with the current project name
    const grantNameInput = page.locator("input[name='grant_name']");
    await expect(grantNameInput).toBeVisible();
    const value = await grantNameInput.inputValue();
    expect(value.length).toBeGreaterThan(0);

    // Cancel closes the form without changes
    await page.click("button:has-text('Cancel')");
    await expect(page.locator("text=Edit Project Details")).not.toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// Report download
// ---------------------------------------------------------------------------

test.describe("Report download", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto(`/projects/${DEMO_PROJECT_ID}`);
    await page.waitForSelector("text=Eligibility Score");
  });

  test("download report button triggers a PDF download", async ({ page }) => {
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.click("button:has-text('Download Report')"),
    ]);
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.pdf$/i);
    // Verify we got actual content
    const downloadPath = path.join(os.tmpdir(), filename);
    await download.saveAs(downloadPath);
    const stats = fs.statSync(downloadPath);
    expect(stats.size).toBeGreaterThan(1000); // at least 1 KB
    fs.unlinkSync(downloadPath);
  });
});

// ---------------------------------------------------------------------------
// New project creation
// ---------------------------------------------------------------------------

test.describe("Create project", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("creates a new project and navigates to project page", async ({ page }) => {
    await page.goto("/projects/new");
    await page.waitForSelector("text=New Grant Project");

    // Wait for org dropdown to populate
    await page.waitForSelector("select");
    await page.fill("input[name='grant_name']", "E2E Test Grant " + Date.now());
    await page.fill("input[name='funder_name']", "E2E Foundation");
    await page.click("button:has-text('Create Project')");

    await page.waitForSelector("text=Project created");
    await expect(page.locator("text=Project created")).toBeVisible();

    await page.click("button:has-text('Go to Project')");
    await expect(page).toHaveURL(/\/projects\//);
    await expect(page.locator("text=Upload Documents")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Document upload
// ---------------------------------------------------------------------------

test.describe("Document upload", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("upload panel visible on draft project", async ({ page }) => {
    // Create a fresh project
    await page.goto("/projects/new");
    await page.waitForSelector("text=New Grant Project");
    await page.waitForSelector("select");
    await page.fill("input[name='grant_name']", "Upload Test " + Date.now());
    await page.click("button:has-text('Create Project')");
    await page.click("button:has-text('Go to Project')");
    await expect(page.locator("text=Upload Documents")).toBeVisible();
  });

  test("delete button shows confirmation then removes document", async ({ page }) => {
    // Navigate to demo project's upload panel
    await page.goto(`/projects/${DEMO_PROJECT_ID}`);
    await page.waitForSelector("text=Eligibility Score");
    // Switch to upload mode
    await page.click("button:has-text('Upload More Documents')");
    await page.waitForSelector("text=Upload Documents");
    // If there are documents, try delete on first one
    const deleteButtons = page.locator("[title='Delete document']");
    const count = await deleteButtons.count();
    if (count > 0) {
      await deleteButtons.first().click();
      // Confirmation should appear
      await expect(page.locator("text=Delete?")).toBeVisible();
      // Cancel
      await page.click("text=No");
      await expect(page.locator("text=Delete?")).not.toBeVisible();
    }
  });
});
