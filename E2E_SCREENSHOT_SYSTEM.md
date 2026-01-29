# 📸 End-to-End Testing with Screenshot System

Complete overview of SpeakEasy's enhanced E2E testing infrastructure with screenshot capabilities.

## 🎯 What We Built

### 1. Screenshot Helper System (`gui/e2e/helpers/screenshot.ts`)
Comprehensive utility for capturing and organizing screenshots:
- Automatic directory management
- Consistent naming conventions
- Organized output by category (test, documentation, failure, feature)
- Manifest generation for tracking all screenshots
- Automatic cleanup of old screenshots
- Support for full-page, element-specific, and masked screenshots

### 2. Systematic Page Tour (`gui/e2e/screenshots/page-tour.test.ts`)
Automated screenshot tour capturing all application pages:
- **Main Pages:** Dashboard, Recording, History, Stats, Batch Transcription
- **Settings Pages:** Model, Audio, Hotkey, Appearance, Behavior, Data, About
- **Key Features:** Sidebar, Recording controls, Search, etc.
- **Empty States:** Documentation of UI states with no data
- **Theme Variations:** Light and dark mode screenshots

### 3. Enhanced Documentation Screenshots (`gui/e2e/screenshots/screenshots-enhanced.test.ts`)
Focused screenshots for GitHub documentation:
- Dashboard with recent transcriptions
- History page with search
- All settings pages
- Recording flow (idle and active states)
- Batch transcription interface
- Statistics dashboard

### 4. Global Setup/Teardown
- **Setup:** Creates screenshot directories, cleans old screenshots, prepares environment
- **Teardown:** Writes manifest, generates summary statistics

### 5. Example Tests (`gui/e2e/examples/integrating-screenshots.test.ts`)
Reference implementations showing:
- Basic screenshot capture
- Before/after screenshots
- Multi-step workflows
- Failure handling
- Feature-specific screenshots
- Automatic test hooks

## 🚀 Quick Start

### Run All Screenshot Tests
```bash
cd gui
npm run test:e2e:screenshots
```

### Run Specific Screenshot Tests
```bash
# Full page tour
npm run test:e2e:page-tour

# Documentation screenshots only
npm run test:e2e:screenshot-docs
```

### View Results
```bash
# View manifest
cat e2e/screenshots/manifest.json

# View summary
cat e2e/screenshots/summary.json

# View actual screenshots
ls e2e/screenshots/documentation/
```

## 📊 Screenshot Output Structure

```
gui/e2e/screenshots/
├── test/           # Screenshots from test runs (keep last 50)
├── documentation/  # Documentation images (never cleaned)
├── failure/        # Test failure screenshots (keep last 50)
├── feature/        # Feature highlight screenshots (keep last 50)
├── manifest.json   # Complete screenshot catalog
└── summary.json    # Statistics and counts
```

## 🔑 Key Features

### ✅ Single Session Reuse
The existing `electron-fixture.ts` already implements session reuse with the `cachedApp` pattern. Tests share a single Electron window, avoiding the overhead of repeatedly spawning the app.

### ✅ Screenshots for All Tests
Every test can now easily capture screenshots at any point:
```typescript
import { captureScreenshot } from '../helpers/screenshot'

await captureScreenshot(page, test.title, {
  description: 'What happened here'
})
```

### ✅ Organized by Category
- **test:** Regular test screenshots (auto-cleanup)
- **documentation:** GitHub docs (never cleaned)
- **failure:** Debugging failures (auto-cleanup)
- **feature:** Feature highlights (auto-cleanup)

### ✅ Automatic Manifest
All screenshots are tracked in `manifest.json` with:
- File path
- Category
- Test name
- Description
- Capture timestamp

### ✅ Systematic Coverage
Page tour captures every application screen automatically, ensuring documentation stays up-to-date.

## 📖 Usage Examples

### Basic Screenshot
```typescript
test('example', async ({ page }) => {
  await page.goto('/')
  await captureScreenshot(page, test.title, {
    description: 'Dashboard loaded'
  })
})
```

### Before/After
```typescript
await captureBeforeScreenshot(page, test.title, { filename: 'before' })
await page.click('#submit')
await captureAfterScreenshot(page, test.title, { filename: 'after' })
```

### Failure Handling
```typescript
try {
  // test code
} catch (error) {
  await captureFailureScreenshot(page, test.title, error)
  throw error
}
```

### Full-Page Documentation
```typescript
await capturePageDocumentation(page, 'Dashboard', {
  description: 'Complete dashboard for documentation'
})
```

## 🔧 Integration with Existing Tests

To add screenshots to existing tests:

1. Import the helper:
   ```typescript
   import { captureScreenshot } from '../helpers/screenshot'
   ```

2. Add screenshots at key points:
   ```typescript
   test('existing test', async ({ page }) => {
     // ... existing test code ...

     await captureScreenshot(page, test.title, {
       description: 'Key moment in test'
     })

     // ... more test code ...
   })
   ```

3. Optionally add test hooks:
   ```typescript
   test.afterEach(async ({ page }, testInfo) => {
     if (testInfo.status !== 'passed') {
       await captureFailureScreenshot(page, testInfo.title)
     }
   })
   ```

## 📚 Documentation Workflow

### Before Release
```bash
# 1. Run full page tour
npm run test:e2e:page-tour

# 2. Run documentation screenshots
npm run test:e2e:screenshot-docs

# 3. Review screenshots
ls e2e/screenshots/documentation/

# 4. Update GitHub docs with new screenshots
```

### Continuous Updates
- Add new pages to `page-tour.test.ts` as features are added
- Run page tour before each release
- Commit documentation screenshots to repository
- Use manifest to track which screenshots need updating

## 🛠️ Configuration

### Adjust Auto-Cleanup
Edit `e2e/global-setup.ts`:
```typescript
// Keep last N screenshots
await cleanupOldScreenshots('test', 50)
await cleanupOldScreenshots('failure', 50)
```

### Viewport Size
Configure in `playwright.config.ts`:
```typescript
viewport: { width: 1280, height: 720 }
```

## 📊 Benefits

1. **Consistent Documentation:** All screenshots captured in same way
2. **Automatic Updates:** Page tour keeps docs current
3. **Debugging Support:** Failure screenshots help debug CI issues
4. **Organized Output:** Easy to find screenshots by purpose
5. **Minimal Overhead:** Single session reuse, smart cleanup
6. **Manifest Tracking:** Complete catalog of all screenshots

## 📝 Next Steps

1. **Run the page tour:** Generate initial set of screenshots
2. **Review output:** Check `gui/e2e/screenshots/documentation/`
3. **Update existing tests:** Add screenshots to key tests using examples
4. **Integrate with CI:** Add screenshot capture to CI pipeline
5. **Publish to docs:** Use manifest to automate doc updates

## 🔍 Troubleshooting

### Screenshots Not Appearing
- Check test output for errors
- Verify directory permissions
- Ensure app is fully loaded before capture

### Poor Quality Screenshots
- Add `waitForTimeout(1000)` before capture
- Use `fullPage: true` for complete pages
- Check viewport configuration

### Too Many Screenshots
- Reduce auto-cleanup threshold
- Remove unnecessary test screenshots
- Focus on documentation category

## 📚 Additional Resources

- **README:** `gui/e2e/screenshots/README.md` - Detailed usage guide
- **Examples:** `gui/e2e/examples/integrating-screenshots.test.ts` - Code examples
- **Helper:** `gui/e2e/helpers/screenshot.ts` - Full API documentation
- **Config:** `gui/playwright.config.ts` - Playwright configuration

---

**Status:** ✅ Complete - Ready to use

Run `npm run test:e2e:page-tour` to capture all application screenshots!
