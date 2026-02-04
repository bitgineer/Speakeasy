/**
 * Window management for SpeakEasy
 * 
 * Handles main dashboard window and recording indicator overlay.
 */

import { BrowserWindow, shell, screen } from 'electron'
import { join } from 'path'
import { is } from '@electron-toolkit/utils'
import { startOverlayTracking, stopOverlayTracking, updatePosition } from './overlay-positioner'

let mainWindow: BrowserWindow | null = null
let recordingIndicator: BrowserWindow | null = null

/**
 * Create the main dashboard window
 */
export function createMainWindow(): BrowserWindow {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    minWidth: 600,
    minHeight: 400,
    show: false,
    autoHideMenuBar: true,
    frame: true,
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#18181b', // surface-900
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // Load the app
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  // Hide instead of close (keep in tray)
  mainWindow.on('close', (event) => {
    if (!mainWindow?.isDestroyed()) {
      event.preventDefault()
      mainWindow?.hide()
    }
  })

  return mainWindow
}

/**
 * Create the recording indicator overlay window
 */
export function createRecordingIndicator(): BrowserWindow {
  const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize

  // Size for the minimal pill UI - will be dynamically resized
  // Start with a reasonable small size, content will resize to fit
  const indicatorWidth = 300
  const indicatorHeight = 80
  const bottomMargin = 50 // Distance from bottom of work area

  recordingIndicator = new BrowserWindow({
    width: indicatorWidth,
    height: indicatorHeight,
    x: Math.round(screenWidth / 2 - indicatorWidth / 2),
    y: screenHeight - indicatorHeight - bottomMargin,
    show: false, // Hidden by default, renderer will show it based on settings
    frame: false,
    transparent: true,
    backgroundColor: '#00000000', // Restore this to fix visibility
    alwaysOnTop: true,
    skipTaskbar: true,
    type: 'toolbar', // Hint to OS that this is a toolbar/overlay
    resizable: false,
    movable: false,
    focusable: false,
    hasShadow: false, // Shadow handled in CSS
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  // Start with pass-through enabled (renderer will toggle when hovering interactive elements)
  recordingIndicator.setIgnoreMouseEvents(true, { forward: true })

  // Start tracking the cursor to keep the overlay on the active display
  startOverlayTracking(recordingIndicator)

  // Clean up tracking when window is closed
  recordingIndicator.on('closed', () => {
    stopOverlayTracking()
    recordingIndicator = null
  })

  // Load the recording indicator page
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    recordingIndicator.loadURL(`${process.env['ELECTRON_RENDERER_URL']}#/recording-indicator`)
  } else {
    recordingIndicator.loadFile(join(__dirname, '../renderer/index.html'), {
      hash: '#/recording-indicator'
    })
  }

  return recordingIndicator
}

/**
 * Show the recording indicator
 */
export function showRecordingIndicator(): void {
  if (recordingIndicator && !recordingIndicator.isDestroyed()) {
    // Enforce "Always On Top" aggressively
    recordingIndicator.setAlwaysOnTop(true, 'screen-saver')
    recordingIndicator.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })
    recordingIndicator.show()
    
    // Ensure it doesn't steal focus (which might lower z-index on some OSs)
    recordingIndicator.setSkipTaskbar(true)
    
    // Ensure position is correct when showing
    updatePosition(recordingIndicator)
  }
}

/**
 * Resize the recording indicator window to fit content
 * Called from renderer when content size changes
 */
export function resizeRecordingIndicator(width: number, height: number): void {
  if (recordingIndicator && !recordingIndicator.isDestroyed()) {
    updatePosition(recordingIndicator, width, height)
  }
}

/**
 * Hide the recording indicator
 */
export function hideRecordingIndicator(): void {
  if (recordingIndicator && !recordingIndicator.isDestroyed()) {
    recordingIndicator.hide()
  }
}

/**
 * Get the main window instance
 */
export function getMainWindow(): BrowserWindow | null {
  return mainWindow
}

/**
 * Get the recording indicator instance
 */
export function getRecordingIndicator(): BrowserWindow | null {
  return recordingIndicator
}

/**
 * Show the main window
 */
export function showMainWindow(): void {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show()
    mainWindow.focus()
  } else {
    createMainWindow()
  }
}

/**
 * Hide the main window
 */
export function hideMainWindow(): void {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.hide()
  }
}
