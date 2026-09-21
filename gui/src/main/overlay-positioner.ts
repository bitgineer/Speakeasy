import { BrowserWindow, screen } from 'electron'

let trackingInterval: NodeJS.Timeout | null = null
let currentDisplayId: number | null = null

/**
 * Start tracking the cursor to keep the overlay on the active display
 */
export function startOverlayTracking(window: BrowserWindow): void {
  stopOverlayTracking()

  // Initial position check
  updatePosition(window)

  // Poll for display changes based on cursor position
  trackingInterval = setInterval(() => {
    if (window.isDestroyed()) {
      stopOverlayTracking()
      return
    }

    const cursor = screen.getCursorScreenPoint()
    const display = screen.getDisplayNearestPoint(cursor)

    if (display.id !== currentDisplayId) {
      updatePosition(window)
    }
  }, 100) // 10Hz is sufficient for display switching, 30-60Hz might be overkill for just switching screens
}

/**
 * Stop tracking the cursor
 */
export function stopOverlayTracking(): void {
  if (trackingInterval) {
    clearInterval(trackingInterval)
    trackingInterval = null
  }
}

/**
 * Update the window position to be centered on the active display
 */
export function updatePosition(window: BrowserWindow, width?: number, height?: number): void {
  if (window.isDestroyed()) return

  const cursor = screen.getCursorScreenPoint()
  const display = screen.getDisplayNearestPoint(cursor)
  
  // Update current display ID
  currentDisplayId = display.id

  const workArea = display.workArea
  const bounds = window.getBounds()
  
  const targetWidth = width || bounds.width
  const targetHeight = height || bounds.height
  const bottomMargin = 20

  const x = Math.round(workArea.x + (workArea.width / 2) - (targetWidth / 2))
  const y = Math.round(workArea.y + workArea.height - targetHeight - bottomMargin)

  window.setBounds({
    x,
    y,
    width: targetWidth,
    height: targetHeight
  })
}

/**
 * Center the window on the active display (alias for updatePosition)
 */
export function centerOnActiveDisplay(window: BrowserWindow): void {
  updatePosition(window)
}
