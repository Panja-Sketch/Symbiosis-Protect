import { defineConfig, devices } from "@playwright/test";

// Starts the API (in-memory store, no scheduler, no emulator) and the web app. Weather is live NWS/Open-Meteo;
// tests that need a specific condition use the Scenario Director so they are deterministic.
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:3100", trace: "retain-on-failure" },
  projects: [
    { name: "phone-390x844", use: { ...devices["Pixel 5"], viewport: { width: 390, height: 844 } } },
    { name: "laptop-1440x900", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  ],
  webServer: [
    {
      command: "uv run uvicorn app.main:app --port 8000",
      cwd: "../api",
      url: "http://127.0.0.1:8000/healthz",
      reuseExistingServer: true,
      timeout: 120_000,
      env: { FIRESTORE_EMULATOR_HOST: "", SCHEDULER_ENABLED: "false", DEMO_MODE: "true" },
    },
    {
      command: "pnpm dev",
      url: "http://localhost:3100/api/healthz",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
