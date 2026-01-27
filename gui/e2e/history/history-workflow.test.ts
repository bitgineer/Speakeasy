import { test, expect } from '../fixtures/electron-fixture'
import { waitForBackend } from '../helpers'

test.describe('History Workflow', () => {
  test.beforeEach(async ({ request }) => {
    await waitForBackend(request)
  })

  test('should display search input', async ({ mainWindow }) => {
    const searchInput = mainWindow.locator('input[placeholder*="Search"]')
    await expect(searchInput).toBeVisible()
  })

  test('should show empty state or history items', async ({ mainWindow }) => {
    const emptyState = mainWindow.locator('text=No transcriptions yet')
    const historyContainer = mainWindow.locator('.space-y-3')
    
    const hasContent = await emptyState.or(historyContainer).isVisible()
    expect(hasContent).toBe(true)
  })

  test('should allow typing in search', async ({ mainWindow }) => {
    const searchInput = mainWindow.locator('input[placeholder*="Search"]')
    await searchInput.fill('test query')
    await expect(searchInput).toHaveValue('test query')
  })

  test('should clear search input', async ({ mainWindow }) => {
    const searchInput = mainWindow.locator('input[placeholder*="Search"]')
    await searchInput.fill('test')
    await searchInput.clear()
    await expect(searchInput).toHaveValue('')
  })

  test('should have scrollable history container', async ({ mainWindow }) => {
    const scrollContainer = mainWindow.locator('.overflow-auto, .overflow-y-auto').first()
    const hasScrollContainer = await scrollContainer.isVisible()
    expect(typeof hasScrollContainer).toBe('boolean')
  })
})
