/**
 * Event utilities for IPC communication
 * 
 * Provides shared functions for sending events to renderer windows.
 */

import { BrowserWindow } from 'electron'

export function sendToRenderer(channel: string, ...args: unknown[]): void {
  BrowserWindow.getAllWindows().forEach((window) => {
    if (!window.isDestroyed()) {
      window.webContents.send(channel, ...args)
    }
  })
}