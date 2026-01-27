/**
 * Playwright Configuration for SpeakEasy Electron E2E Testing
 * 
 * CRITICAL: Electron requires single worker and no parallel execution
 * to prevent multiple Electron instances from conflicting.
 */

import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  
  // CRITICAL: Electron cannot run multiple instances
  fullyParallel: false,
  workers: 1,

  retries: process.env.CI ? 2 : 0,

  reporter: [
    ['html', { open: 'never' }],
    ['list']
  ],

  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000
  },

  outputDir: './e2e-results',
})
