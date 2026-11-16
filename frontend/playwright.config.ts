import { defineConfig, devices } from "@playwright/test";

// E2E_BASE_URL set = test a live site (Netlify): no local servers are started.
const live = process.env.E2E_BASE_URL;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: live ?? "http://localhost:5173",
    trace: "retain-on-failure",
    // A fresh browser has no saved language or theme: tests start in English, light.
    locale: "en-GB",
    colorScheme: "light",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: live
    ? undefined
    : [
        {
          command: "cd ../backend && uv run --no-sync uvicorn app.main:app --port 8000",
          url: "http://localhost:8000/api/health",
          reuseExistingServer: true,
          timeout: 120_000,
        },
        {
          command: "pnpm dev --port 5173 --strictPort",
          url: "http://localhost:5173",
          reuseExistingServer: true,
          timeout: 120_000,
        },
      ],
});
