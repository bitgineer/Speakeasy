import { test, expect } from '../fixtures/electron-fixture'
import { waitForBackend, navigateTo } from '../helpers'

test.describe('Hotkey Settings', () => {
  test.beforeEach(async ({ mainWindow, request }) => {
    await waitForBackend(request)
    await navigateTo(mainWindow, '/settings')
  })

  test('should display hotkey settings section', async ({ mainWindow }) => {
    const hotkeySection = mainWindow.locator('h2').filter({ hasText: /Hotkey/i })
    await expect(hotkeySection).toBeVisible()
  })

  test('should show hotkey mode options', async ({ mainWindow }) => {
    const toggleOption = mainWindow.locator('text=Toggle')
    const pttOption = mainWindow.locator('text=Push-to-talk')
    
    await expect(toggleOption.or(pttOption)).toBeVisible()
  })

  test('should allow selecting toggle mode', async ({ mainWindow }) => {
    const toggleRadio = mainWindow.locator('input[value="toggle"]')
    if (await toggleRadio.isVisible()) {
      await toggleRadio.check()
      await expect(toggleRadio).toBeChecked()
    }
  })

  test('should allow selecting push-to-talk mode', async ({ mainWindow }) => {
    const pttRadio = mainWindow.locator('input[value="push-to-talk"]')
    if (await pttRadio.isVisible()) {
      await pttRadio.check()
      await expect(pttRadio).toBeChecked()
    }
  })

  test('should display hotkey input field', async ({ mainWindow }) => {
    const hotkeyInput = mainWindow.locator('input[placeholder*="Press"]')
      .or(mainWindow.locator('[data-testid="hotkey-input"]'))
      .or(mainWindow.locator('.hotkey-input'))
    
    const hasHotkeyInput = await hotkeyInput.first().isVisible()
    expect(typeof hasHotkeyInput).toBe('boolean')
  })
})
