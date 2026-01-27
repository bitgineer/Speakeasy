# Phase 06: E2E Testing with Electron Driver

This phase implements end-to-end testing that validates the entire application from the user's perspective. Using Spectron or Electron's custom driver, these tests verify that the backend and frontend work together correctly, simulating real user workflows like recording, transcribing, and managing settings.

## Tasks

- [ ] Set up E2E testing infrastructure:
  - Add `@electron/fuses` and Electron driver dependencies to `gui/package.json`
  - Create `gui/e2e/` directory for E2E tests
  - Create `gui/e2e/setup.ts` for test environment initialization
  - Create `wdio.conf.js` or `electron-mocha` configuration
  - Add E2E test scripts to `gui/package.json`

- [ ] Create E2E test utilities:
  - Create `gui/e2e/helpers.ts` with reusable helper functions
  - Add `startApp()` helper to launch Electron app in test mode
  - Add `stopApp()` helper for cleanup
  - Add `waitForElement()` helper for waiting on UI elements
  - Add `mockBackend()` helper to start backend test server

- [ ] Create E2E test for app launch:
  - Create `gui/e2e/basic/app-launch.test.ts`
  - Verify app starts without crashes
  - Verify main window appears
  - Verify backend connection is established
  - Verify health status shows as "ok"

- [ ] Create E2E test for settings workflow:
  - Create `gui/e2e/settings/settings-workflow.test.ts`
  - Navigate to Settings page
  - Select different model type
  - Change device selection
  - Save settings
  - Verify save confirmation appears
  - Restart app and verify settings persist

- [ ] Create E2E test for recording workflow:
  - Create `gui/e2e/recording/recording-workflow.test.ts`
  - Pre-load a mock model for testing
  - Start recording via hotkey
  - Verify recording indicator appears
  - Stop recording
  - Verify transcription completes
  - Verify result appears in history

- [ ] Create E2E test for history management:
  - Create `gui/e2e/history/history-workflow.test.ts`
  - Populate test history with sample data
  - Verify items appear in Dashboard
  - Test search functionality
  - Test deleting an item
  - Test pagination/load more

- [ ] Create E2E test for error handling:
  - Create `gui/e2e/errors/error-handling.test.ts`
  - Test behavior when backend is unreachable
  - Test behavior when model fails to load
  - Test behavior when recording device is unavailable
  - Verify appropriate error messages appear

- [ ] Create E2E test for hotkey functionality:
  - Create `gui/e2e/hotkey/hotkey-test.ts`
  - Register a test hotkey
  - Simulate hotkey press
  - Verify recording starts
  - Simulate second press (toggle mode)
  - Verify recording stops

- [ ] Add visual regression testing (optional but valuable):
  - Set up Percy or similar visual regression tool
  - Capture screenshots of key pages: Dashboard, Settings
  - Add screenshots to various states: recording, error, loading
  - Configure baseline comparisons

- [ ] Create E2E test documentation:
  - Create `gui/e2e/README.md` explaining how to run E2E tests
  - Document test architecture and helpers
  - Add troubleshooting guide for common failures
  - Document how to add new E2E tests

- [ ] Run and validate all E2E tests:
  - Execute full E2E test suite
  - Fix any flaky or failing tests
  - Ensure tests complete in reasonable time (<5 minutes)
  - Verify tests work on Windows, macOS, and Linux if possible
