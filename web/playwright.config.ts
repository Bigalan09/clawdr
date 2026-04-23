import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: "http://localhost:3000",
    headless: true,
  },
  webServer: [
    {
      command: "cd ../backend && uv run uvicorn clawdr.main:app --port 8000",
      port: 8000,
      reuseExistingServer: true,
      timeout: 15_000,
    },
    {
      command: "bun dev --port 3000",
      port: 3000,
      reuseExistingServer: true,
      timeout: 15_000,
    },
  ],
});
