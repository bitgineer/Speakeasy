/**
 * SpeakEasy - Electron Main Process Entry
 * 
 * Handles app lifecycle, window management, and backend process coordination.
 */

import { app, BrowserWindow, dialog } from 'electron'
import { electronApp, optimizer } from '@electron-toolkit/utils'
import { createTray, destroyTray } from './tray'
import { createMainWindow, createRecordingIndicator, getMainWindow, setQuitting } from './windows'
import { startBackend, stopBackend, MissingBackendEnvironmentError } from './backend'
import { setupIpcHandlers } from './ipc-handlers'
import { unregisterGlobalHotkey, stopUiohook } from './hotkey'

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
      if (error instanceof MissingBackendEnvironmentError) {
        dialog.showErrorBox(
          'SpeakEasy cannot start',
          'This build does not include the Python backend, and no backend environment was found.\n\n' +
            'SpeakEasy is distributed through its source setup. Run install.bat on Windows, or ' +
            './install.sh on macOS and Linux, from the repository, then start the app from there.'
        )
        app.quit()
        return
      }
      console.error('Failed to start backend:', error)
      // Continue anyway - backend might be running externally in dev
    }

    // Create windows
    createMainWindow()
    createRecordingIndicator()
    // showRecordingIndicator() - Removed to respect initial settings (hidden by default)
    
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
    setQuitting(true)
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
