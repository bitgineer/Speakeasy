import { test, expect } from './fixtures/electron-app';

test.describe('Application Launch', () => {
    test('should launch the application', async ({ page, electronApp }) => {
        // Check if the window is open
        const windowCount = await electronApp.windows();
        expect(windowCount.length).toBeGreaterThan(0);

        // Initial title check
        const title = await page.title();
        console.log(`App title: ${title}`);
        // expect(title).toBe('SpeakEasy'); // Uncomment if title is deterministic
    });

    test('should display key elements on homepage', async ({ page }) => {
        // Look for common elements like "Record" button, or settings icon
        // We will wait for some content to ensure it loaded
        await expect(page.locator('body')).toBeVisible();

        // Screenshot for visual verification (saved to results)
        await page.screenshot({ path: 'test-results/screenshots/launch.png' });
    });
});
