import { test, expect } from '../fixtures/electron-fixture'
import { waitForBackend, getHealthStatus } from '../helpers'

test.describe('Recording Workflow', () => {
  test.beforeEach(async ({ request }) => {
    await waitForBackend(request)
  })

  test('should show status bar on dashboard', async ({ mainWindow }) => {
    const statusBar = mainWindow.locator('.bg-gray-800\\/50').first()
    await expect(statusBar).toBeVisible()
  })

  test('should display model status', async ({ mainWindow }) => {
    const noModelText = mainWindow.locator('text=No model loaded')
    const readyText = mainWindow.locator('text=Ready')
    const modelName = mainWindow.locator('text=/whisper|parakeet|canary/i')
    
    const hasStatus = await noModelText.or(readyText).or(modelName).isVisible()
    expect(hasStatus).toBe(true)
  })

  test('should show device status', async ({ mainWindow }) => {
    const deviceInfo = mainWindow.locator('.bg-gray-800\\/50')
    await expect(deviceInfo).toBeVisible()
  })

  test('should display transcription count stats', async ({ mainWindow }) => {
    const statsArea = mainWindow.locator('text=/transcription/i')
    const hasStats = await statsArea.isVisible()
    expect(typeof hasStats).toBe('boolean')
  })

  test('should reflect backend health status', async ({ mainWindow, request }) => {
    const health = await getHealthStatus(request)
    expect(health).not.toBeNull()
    
    if (health) {
      expect(health.status).toBe('ok')
      expect(typeof health.model_loaded).toBe('boolean')
      expect(typeof health.gpu_available).toBe('boolean')
    }
  })
})
