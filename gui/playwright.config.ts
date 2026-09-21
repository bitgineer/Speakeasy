import { defineConfig, devices } from '@playwright/test'
import path from 'path'

/**
 * Playwright Configuration for Electron E2E Tests
 *
 * Key Features:
 * - Single worker (required for Electron)
 * - Screenshots captured for all tests (not just failures)
 * - Video recording for debugging
 * - Trace retention for failed tests
 * - Organized screenshot output by category
 */

export default defineConfig({
  testDir: './e2e',

  // Electron-specific configuration
  workers: 1, // Single worker required for Electron
  timeout: 30_000, // 30 seconds per test
  expect: {
    timeout: 5000
  },

  // Test output organization
  outputDir: 'test-results',
  reporter: [
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['html', { outputFolder: 'test-results/html-report' }]
  ],

  // Retry failed tests
  retries: process.env.CI ? 2 : 0,

  // Screenshot configuration
  use: {
    // Capture screenshots at different stages
    screenshot: 'only-on-failure', // Fallback: automatic screenshots on failure
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    // Browser context options
    viewport: { width: 1280, height: 720 },
    // Action timeouts
    actionTimeout: 10000,
    navigationTimeout: 10000
  },

  // Projects for different test scenarios
  projects: [
    {
      name: 'e2e',
      use: {
        ...devices['Desktop Chrome']
      }
    }
  ],

  // Global setup and teardown
  globalSetup: require.resolve('./e2e/global-setup.ts'),
  globalTeardown: require.resolve('./e2e/global-teardown.ts'),

  // Metadata for organization
  metadata: {
    app: 'SpeakEasy',
    version: require('./package.json').version
  },

  // Web server (not needed for Electron but useful for debugging)
  webServer: process.env.WEB_SERVER
    ? {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      timeout: 120 * 1000,
      reuseExistingServer: true
    }
    : undefined
})
