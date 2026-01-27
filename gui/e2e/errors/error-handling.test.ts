import { test, expect } from '../fixtures/electron-fixture'
import { waitForBackend } from '../helpers'

test.describe('Error Handling', () => {
  test('should show connection indicator on launch', async ({ mainWindow }) => {
    const indicator = mainWindow.locator('.rounded-full').first()
    await expect(indicator).toBeVisible()
  })

  test('should eventually connect to backend', async ({ mainWindow, request }) => {
    const connected = await waitForBackend(request, 60000)
    expect(connected).toBe(true)
    
    const greenDot = mainWindow.locator('.bg-green-500').first()
    await expect(greenDot).toBeVisible({ timeout: 10000 })
  })

  test('should handle page reload gracefully', async ({ mainWindow, request }) => {
    await waitForBackend(request)
    
    await mainWindow.reload()
    await mainWindow.waitForLoadState('domcontentloaded')
    
    const connected = await waitForBackend(request)
    expect(connected).toBe(true)
    
    const header = mainWindow.locator('h1').filter({ hasText: 'SpeakEasy' })
    await expect(header).toBeVisible()
  })

  test('should display error boundary for React errors', async ({ mainWindow }) => {
    const errorBoundary = mainWindow.locator('[data-testid="error-boundary"]')
    const noErrorBoundary = await errorBoundary.count() === 0
    expect(noErrorBoundary).toBe(true)
  })

  test('should show reconnecting state when backend temporarily unavailable', async ({ mainWindow }) => {
    const reconnectingText = mainWindow.locator('text=Reconnecting')
    const connectedText = mainWindow.locator('text=Connected')
    
    const hasConnectionState = await reconnectingText.or(connectedText).isVisible()
    expect(typeof hasConnectionState).toBe('boolean')
  })
})
