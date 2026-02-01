import { FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

export default async function globalSetup(config: FullConfig) {
    console.log('\n🔧 Running global E2E test setup...');

    // Ensure screenshot directories exist
    const screenshotDir = path.join(__dirname, '../test-results/screenshots');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
        console.log('  ✅ Created screenshot directory');
    }

    console.log('✅ Global E2E test setup complete\n');
}
