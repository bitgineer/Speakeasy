/**
 * SpeakEasy - Electron Main Process Entry
 * 
 * Handles app lifecycle, window management, and backend process coordination.
 */

import { app, BrowserWindow, ipcMain } from 'electron'
import { electronApp, optimizer } from '@electron-toolkit/utils'
import { join } from 'path'
import { createTray, destroyTray } from './tray'
import { createMainWindow, createRecordingIndicator, getMainWindow, getRecordingIndicator, showRecordingIndicator } from './windows'
import { startBackend, stopBackend, isBackendRunning } from './backend'
import { setupIpcHandlers } from './ipc-handlers'
import { registerGlobalHotkey, unregisterGlobalHotkey, stopUiohook } from './hotkey'

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock()

if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    // Focus the main window if a second instance is launched
    const mainWindow = getMainWindow()
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })

  // App ready handler
  app.whenReady().then(async () => {
    // Set app user model id for windows
    electronApp.setAppUserModelId('com.speakeasy.app')

    // Default open or close DevTools by F12 in development
    // and ignore CommandOrControl + R in production.
    app.on('browser-window-created', (_, window) => {
      optimizer.watchWindowShortcuts(window)
    })

    // Setup IPC handlers before creating windows
    setupIpcHandlers()

    // Start Python backend
    try {
      await startBackend()
      console.log('Backend started successfully')
    } catch (error) {
      console.error('Failed to start backend:', error)
      // Continue anyway - backend might be running externally in dev
    }

    // Create windows
    createMainWindow()
    createRecordingIndicator()
    showRecordingIndicator() // Ensure it's shown and positioned correctly
    
    // Create system tray
    createTray()

    // Register global hotkey (will be configured from settings)
    // registerGlobalHotkey() - Called after settings are loaded

    app.on('activate', () => {
      // On macOS, re-create window when dock icon is clicked
      if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow()
      }
    })
  })

  // Handle app quit
  app.on('before-quit', async () => {
    console.log('[BEFORE-QUIT] Starting shutdown sequence...')
    console.log('[BEFORE-QUIT] Unregistering global hotkey...')
    unregisterGlobalHotkey()
    console.log('[BEFORE-QUIT] Hotkey unregistered. Stopping uiohook...')
    stopUiohook()
    console.log('[BEFORE-QUIT] Uiohook stopped. Stopping backend...')
    await stopBackend()
    console.log('[BEFORE-QUIT] Backend stopped. Destroying tray...')
    destroyTray()
    console.log('[BEFORE-QUIT] Shutdown complete!')
  })

  // Quit when all windows are closed, except on macOS
  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      // Don't quit - keep running in tray
      // app.quit()
    }
  })
}
