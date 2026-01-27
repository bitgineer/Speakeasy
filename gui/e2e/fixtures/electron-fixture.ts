import { test as base, _electron as electron } from '@playwright/test'
import type { ElectronApplication, Page } from '@playwright/test'
import path from 'path'

type ElectronFixtures = {
  electronApp: ElectronApplication
  mainWindow: Page
}

export const test = base.extend<ElectronFixtures>({
  electronApp: async ({}, use) => {
    const mainPath = path.join(__dirname, '../../out/main/index.js')
    
    const app = await electron.launch({
      args: [mainPath],
      env: { 
        ...process.env, 
        NODE_ENV: 'test',
        SPEAKEASY_TEST_MODE: '1'
      }
    })
    
    await use(app)
    await app.close()
  },

  mainWindow: async ({ electronApp }, use) => {
    const window = await electronApp.firstWindow()
    await window.waitForLoadState('domcontentloaded')
    await use(window)
  }
})

export { expect } from '@playwright/test'
