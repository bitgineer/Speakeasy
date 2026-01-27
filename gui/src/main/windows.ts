/**
 * Window management for SpeakEasy
 * 
 * Handles main dashboard window and recording indicator overlay.
 */

import { BrowserWindow, shell, screen } from 'electron'
import { join } from 'path'
import { is } from '@electron-toolkit/utils'

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

  recordingIndicator = new BrowserWindow({
    width: 200,
    height: 60,
    x: Math.round(screenWidth / 2 - 100),
    y: Math.round(screenHeight / 2 - 30),
    show: false,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    movable: false,
    focusable: false,
    hasShadow: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  // Ignore mouse events so it doesn't interfere with user input
  recordingIndicator.setIgnoreMouseEvents(true)

  // Load the recording indicator page
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    recordingIndicator.loadURL(`${process.env['ELECTRON_RENDERER_URL']}#/recording-indicator`)
  } else {
    recordingIndicator.loadFile(join(__dirname, '../renderer/index.html'), {
      hash: '/recording-indicator'
    })
  }

  return recordingIndicator
}

/**
 * Show the recording indicator
 */
export function showRecordingIndicator(): void {
  if (recordingIndicator && !recordingIndicator.isDestroyed()) {
    // Re-center the indicator
    const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize
    recordingIndicator.setPosition(
      Math.round(screenWidth / 2 - 100),
      Math.round(screenHeight / 2 - 30)
    )
    recordingIndicator.show()
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
