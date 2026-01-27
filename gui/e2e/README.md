# E2E Testing for SpeakEasy

End-to-end tests for the SpeakEasy Electron application using Playwright.

## Prerequisites

- Node.js 18+
- Built application: `npm run build`
- Backend auto-starts with app (or run manually: `cd ../backend && python -m speakeasy.server`)

## Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with visible browser window
npm run test:e2e:headed

# Run in debug mode (step through tests)
npm run test:e2e:debug

# View HTML test report
npm run test:e2e:report
```

## Test Suites

| Suite | Path | Description |
|-------|------|-------------|
| Basic | `e2e/basic/` | App launch, window display, navigation |
| Settings | `e2e/settings/` | Settings page workflows |
| Recording | `e2e/recording/` | Recording status and model state |
| History | `e2e/history/` | Transcription history list and search |
| Errors | `e2e/errors/` | Error handling and recovery |
| Hotkey | `e2e/hotkey/` | Hotkey configuration |

## Project Structure

```
e2e/
├── fixtures/
│   └── electron-fixture.ts   # Custom Playwright fixtures for Electron
├── helpers.ts                # Utility functions
├── basic/
│   └── app-launch.test.ts
├── settings/
│   └── settings-workflow.test.ts
├── recording/
│   └── recording-workflow.test.ts
├── history/
│   └── history-workflow.test.ts
├── errors/
│   └── error-handling.test.ts
├── hotkey/
│   └── hotkey-test.ts
└── README.md
```

## Adding New Tests

1. Create test file in appropriate suite directory
2. Import fixtures: `import { test, expect } from '../fixtures/electron-fixture'`
3. Import helpers: `import { waitForBackend, navigateTo } from '../helpers'`
4. Use `test.describe()` and `test()` blocks

Example:

```typescript
import { test, expect } from '../fixtures/electron-fixture'
import { waitForBackend } from '../helpers'

test.describe('My Feature', () => {
  test.beforeEach(async ({ request }) => {
    await waitForBackend(request)
  })

  test('should do something', async ({ mainWindow }) => {
    await expect(mainWindow.locator('selector')).toBeVisible()
  })
})
```

## Debugging

```bash
# Run specific test file
npm run test:e2e -- e2e/basic/app-launch.test.ts

# Run tests matching pattern
npm run test:e2e -- -g "should display"

# Generate trace for debugging
npm run test:e2e -- --trace on
```

## Known Limitations

- **Global hotkeys**: Cannot test actual hotkey triggering (OS-level via uiohook-napi)
- **Audio recording**: Tests verify UI state only, not actual audio capture
- **Model loading**: Tests don't load models (too slow for E2E)

## CI/CD

For CI environments (Linux without display):

```bash
xvfb-run npm run test:e2e
```

Playwright handles most CI setup automatically.
