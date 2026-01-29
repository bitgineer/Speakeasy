import { test, expect } from './fixtures/electron-app';

test.describe('Settings', () => {
    test('should navigate to settings pages', async ({ page }) => {
        // Click on "Model" in the sidebar (first item in settings)
        await page.click('text=Model');

        // Should be at /settings/model
        await expect(page).toHaveURL(/.*#\/settings\/model/);

        // Verify Model Settings header or content exists
        // We check for some text likely to be on the Model settings page
        // or just the URL is enough for navigation test if content is dynamic.
        // Let's check for "Model" text again which should be in the header or breadcrumb if exists.
        // Or check if the "Model" link is active (Sidebar logic).

        // Navigate to Appearance
        await page.click('text=Appearance');
        await expect(page).toHaveURL(/.*#\/settings\/appearance/);

        // Check if we are on appearance page
        // Using a more specific check if possible, but URL check is robust for routing.

        await page.screenshot({ path: 'test-results/screenshots/settings.png' });
    });
});
