import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for GrantPilot end-to-end tests.
 *
 * Assumes both servers are already running:
 *   Frontend: http://localhost:3000  (npm run dev in frontend/)
 *   Backend:  http://localhost:8000  (uvicorn in backend/)
 *
 * Run with: npx playwright test
 * Install browsers first: npx playwright install chromium
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,  // run sequentially to avoid server contention
  retries: 1,
  timeout: 30_000,
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "off",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Expect both dev servers to be running when tests execute.
  // Start them manually before running tests.
});
