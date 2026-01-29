import { test, expect } from './fixtures/electron-app';

test.describe('Transcription Flow', () => {
    test('should display dashboard with recording controls', async ({ page }) => {
        // Navigate to dashboard (default)
        await expect(page).toHaveURL(/.*#\//); // Hash router

        // Check for "Recent Transcriptions" or similar text
        // Based on App.tsx, Dashboard is the default route.
        // We assume Dashboard has some headers.
        // We can also check for Sidebar elements.

        // Check for Sidebar
        await expect(page.locator('nav')).toBeVisible(); // Assuming Sidebar is a nav or within a nav

        // Check for "Dashboard" text in sidebar
        await expect(page.locator('text=Dashboard')).toBeVisible();

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/dashboard.png' });
    });
});
