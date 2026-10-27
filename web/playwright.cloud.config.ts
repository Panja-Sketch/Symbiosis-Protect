import { defineConfig, devices } from "@playwright/test";

// Same specs against the deployed app: BASE_URL=https://... API_URL=https://... SESSION_SECRET=... pnpm exec playwright test -c playwright.cloud.config.ts
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: process.env.BASE_URL, trace: "retain-on-failure" },
  projects: [
    { name: "phone-390x844", use: { ...devices["Pixel 5"], viewport: { width: 390, height: 844 } } },
    { name: "laptop-1440x900", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  ],
});
