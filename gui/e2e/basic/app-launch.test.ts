import { test, expect } from '../fixtures/electron-fixture'
import { waitForBackend } from '../helpers'

test.describe('App Launch', () => {
  test('should display main window with correct title', async ({ mainWindow }) => {
    await expect(mainWindow).toHaveTitle(/SpeakEasy/)
  })

  test('should connect to backend', async ({ mainWindow, request }) => {
    const connected = await waitForBackend(request)
    expect(connected).toBe(true)
  })

  test('should show SpeakEasy header', async ({ mainWindow }) => {
    const header = mainWindow.locator('h1').filter({ hasText: 'SpeakEasy' })
    await expect(header).toBeVisible()
  })

  test('should display connection status indicator', async ({ mainWindow }) => {
    const statusIndicator = mainWindow.locator('.rounded-full').first()
    await expect(statusIndicator).toBeVisible()
  })

  test('should show green connection indicator when backend connected', async ({ mainWindow, request }) => {
    await waitForBackend(request)
    await mainWindow.waitForTimeout(1000)
    const greenDot = mainWindow.locator('.bg-green-500').first()
    await expect(greenDot).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to settings page', async ({ mainWindow }) => {
    await mainWindow.click('a[href="#/settings"]')
    const settingsHeader = mainWindow.locator('h1').filter({ hasText: 'Settings' })
    await expect(settingsHeader).toBeVisible()
  })

  test('should navigate back from settings to dashboard', async ({ mainWindow }) => {
    await mainWindow.click('a[href="#/settings"]')
    await mainWindow.waitForSelector('h1:has-text("Settings")')
    
    const backButton = mainWindow.locator('button').filter({ has: mainWindow.locator('svg') }).first()
    await backButton.click()
    
    const dashboardHeader = mainWindow.locator('h1').filter({ hasText: 'SpeakEasy' })
    await expect(dashboardHeader).toBeVisible()
  })
})
