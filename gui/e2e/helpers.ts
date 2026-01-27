import type { Page, APIRequestContext } from '@playwright/test'

const BACKEND_URL = 'http://127.0.0.1:8765'

export function getBackendUrl(): string {
  return BACKEND_URL
}

export async function waitForBackend(
  requestContext: APIRequestContext,
  timeout = 30000
): Promise<boolean> {
  const startTime = Date.now()
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await requestContext.get(`${BACKEND_URL}/api/health`)
      if (response.ok()) {
        const data = await response.json()
        if (data.status === 'ok') return true
      }
    } catch {
    }
    await new Promise(resolve => setTimeout(resolve, 500))
  }
  
  return false
}

export async function navigateTo(page: Page, route: string): Promise<void> {
  const currentUrl = page.url()
  const baseUrl = currentUrl.split('#')[0]
  await page.goto(`${baseUrl}#${route}`)
  await page.waitForLoadState('domcontentloaded')
}

export async function waitForElement(
  page: Page,
  selector: string,
  options?: { timeout?: number; state?: 'visible' | 'attached' | 'hidden' }
): Promise<void> {
  await page.locator(selector).waitFor({
    timeout: options?.timeout ?? 5000,
    state: options?.state ?? 'visible'
  })
}

export async function getHealthStatus(requestContext: APIRequestContext): Promise<{
  status: string
  state: string
  model_loaded: boolean
  gpu_available: boolean
} | null> {
  try {
    const response = await requestContext.get(`${BACKEND_URL}/api/health`)
    if (response.ok()) {
      return await response.json()
    }
  } catch {
    return null
  }
  return null
}
