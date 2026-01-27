/**
 * IPC Handlers for main process
 * 
 * Bridges renderer process requests to main process functionality.
 */

import { ipcMain, dialog, app } from 'electron'
import { showMainWindow, hideMainWindow, showRecordingIndicator, hideRecordingIndicator } from './windows'
import { isBackendRunning, getBackendPort } from './backend'
import { registerGlobalHotkey, unregisterGlobalHotkey, getCurrentHotkey, getHotkeyMode } from './hotkey'

/**
 * Setup all IPC handlers
 */
export function setupIpcHandlers(): void {
  // Window controls
  ipcMain.handle('window:show', () => {
    showMainWindow()
  })

  ipcMain.handle('window:hide', () => {
    hideMainWindow()
  })

  // Recording indicator controls
  ipcMain.handle('indicator:show', () => {
    showRecordingIndicator()
  })

  ipcMain.handle('indicator:hide', () => {
    hideRecordingIndicator()
  })

  // Backend status
  ipcMain.handle('backend:status', () => {
    return {
      running: isBackendRunning(),
      port: getBackendPort()
    }
  })

  ipcMain.handle('backend:port', () => {
    return getBackendPort()
  })

  // Hotkey management
  ipcMain.handle('hotkey:register', async (_, hotkey: string, mode: 'toggle' | 'push-to-talk' = 'toggle') => {
    try {
      registerGlobalHotkey(hotkey, mode)
      return { success: true }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  })

  ipcMain.handle('hotkey:unregister', () => {
    unregisterGlobalHotkey()
    return { success: true }
  })

  ipcMain.handle('hotkey:current', () => {
    return { hotkey: getCurrentHotkey(), mode: getHotkeyMode() }
  })

  // App info
  ipcMain.handle('app:version', () => {
    return app.getVersion()
  })

  ipcMain.handle('app:quit', () => {
    app.quit()
  })

  // Dialogs
  ipcMain.handle('dialog:showError', async (_, title: string, content: string) => {
    await dialog.showErrorBox(title, content)
  })

  ipcMain.handle('dialog:showMessage', async (_, options: Electron.MessageBoxOptions) => {
    return dialog.showMessageBox(options)
  })
}

/**
 * Send event to all renderer windows
 */
export function sendToRenderer(channel: string, ...args: unknown[]): void {
  const { BrowserWindow } = require('electron')
  BrowserWindow.getAllWindows().forEach((window) => {
    if (!window.isDestroyed()) {
      window.webContents.send(channel, ...args)
    }
  })
}
