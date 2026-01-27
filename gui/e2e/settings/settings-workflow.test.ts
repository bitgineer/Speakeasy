import { test, expect } from '../fixtures/electron-fixture'
import { waitForBackend, navigateTo } from '../helpers'

test.describe('Settings Workflow', () => {
  test.beforeEach(async ({ mainWindow, request }) => {
    await waitForBackend(request)
    await navigateTo(mainWindow, '/settings')
  })

  test('should load settings page', async ({ mainWindow }) => {
    const header = mainWindow.locator('h1').filter({ hasText: 'Settings' })
    await expect(header).toBeVisible()
  })

  test('should display model type selector', async ({ mainWindow }) => {
    const modelSection = mainWindow.locator('h2').filter({ hasText: 'Model' })
    await expect(modelSection).toBeVisible()
  })

  test('should display language dropdown', async ({ mainWindow }) => {
    const languageSection = mainWindow.locator('h2').filter({ hasText: 'Language' })
    await expect(languageSection).toBeVisible()
  })

  test('should display device selector', async ({ mainWindow }) => {
    const deviceSection = mainWindow.locator('h2').filter({ hasText: 'Audio' })
    await expect(deviceSection).toBeVisible()
  })

  test('should have save button', async ({ mainWindow }) => {
    const saveButton = mainWindow.locator('button').filter({ hasText: 'Save' })
    await expect(saveButton).toBeVisible()
  })

  test('should enable save button when settings change', async ({ mainWindow }) => {
    const languageSelect = mainWindow.locator('select').nth(2)
    if (await languageSelect.isVisible()) {
      await languageSelect.selectOption({ index: 1 })
      const saveButton = mainWindow.locator('button').filter({ hasText: 'Save' })
      await expect(saveButton).toBeEnabled()
    }
  })

  test('should navigate back to dashboard', async ({ mainWindow }) => {
    const backButton = mainWindow.locator('button').filter({ has: mainWindow.locator('svg') }).first()
    await backButton.click()
    
    const dashboardHeader = mainWindow.locator('h1').filter({ hasText: 'SpeakEasy' })
    await expect(dashboardHeader).toBeVisible()
  })
})
