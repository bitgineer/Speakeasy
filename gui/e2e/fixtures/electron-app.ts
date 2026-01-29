import { _electron as electron, ElectronApplication, Page, test as base } from '@playwright/test';
import path from 'path';

type WorkerFixtures = {
    electronApp: ElectronApplication;
};

type TestFixtures = {
    page: Page;
};

export const test = base.extend<TestFixtures, WorkerFixtures>({
    electronApp: [async ({ }, use) => {
        // Launch Electron app once per worker
        const mainScript = path.join(__dirname, '../../out/main/index.js');
        console.log(`Launching Electron app with main script: ${mainScript}`);

        const electronApp = await electron.launch({
            args: [mainScript],
            env: {
                ...process.env,
                NODE_ENV: 'test',
            }
        });

        await use(electronApp);

        // Close app after all tests in this worker are done
        await electronApp.evaluate(({ app }) => {
            app.quit();
        });
    }, { scope: 'worker' }],

    page: async ({ electronApp }, use) => {
        const page = await electronApp.firstWindow();

        // Wait for the window to load
        await page.waitForLoadState('domcontentloaded');

        await use(page);
    },
});

export { expect } from '@playwright/test';
