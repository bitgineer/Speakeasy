import { FullConfig } from '@playwright/test';

export default async function globalTeardown(config: FullConfig) {
    console.log('🔧 Running global E2E test teardown...');
    // Add cleanup logic here if needed
    console.log('✅ Global E2E test teardown complete');
}
