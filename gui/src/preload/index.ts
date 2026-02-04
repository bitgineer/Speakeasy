/**
 * Preload Script - Exposes safe APIs to renderer
 * 
 * Uses contextBridge to expose limited IPC functionality to the renderer process.
 */

import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom API exposed to renderer
const api = {
  // Window controls
  showWindow: () => ipcRenderer.invoke('window:show'),
  hideWindow: () => ipcRenderer.invoke('window:hide'),
  
  // Recording indicator
  showIndicator: () => ipcRenderer.invoke('indicator:show'),
  hideIndicator: () => ipcRenderer.invoke('indicator:hide'),
  resizeIndicator: (width: number, height: number) => ipcRenderer.invoke('indicator:resize', width, height),
  setIgnoreMouseEvents: (ignore: boolean, options?: { forward: boolean }) => ipcRenderer.invoke('indicator:setIgnoreMouseEvents', ignore, options),
  startRecording: () => ipcRenderer.invoke('recording:start'),
  stopRecording: () => ipcRenderer.invoke('recording:stop'),
  cancelRecording: () => ipcRenderer.invoke('recording:cancel'),
  
  // Backend
  getBackendStatus: () => ipcRenderer.invoke('backend:status'),
  getBackendPort: () => ipcRenderer.invoke('backend:port'),
  
  // Hotkey
  registerHotkey: (hotkey: string, mode: 'toggle' | 'push-to-talk' = 'toggle') => 
    ipcRenderer.invoke('hotkey:register', hotkey, mode),
  unregisterHotkey: () => ipcRenderer.invoke('hotkey:unregister'),
  getCurrentHotkey: () => ipcRenderer.invoke('hotkey:current'),
  
  // App
  getVersion: () => ipcRenderer.invoke('app:version'),
  quit: () => ipcRenderer.invoke('app:quit'),
  
  // Dialogs
  showError: (title: string, content: string) => 
    ipcRenderer.invoke('dialog:showError', title, content),
  showMessage: (options: Electron.MessageBoxOptions) =>
    ipcRenderer.invoke('dialog:showMessage', options),
  
  // Event listeners
  onNavigate: (callback: (path: string) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, path: string) => callback(path)
    ipcRenderer.on('navigate', handler)
    return () => ipcRenderer.removeListener('navigate', handler)
  },
  
  onRecordingStart: (callback: () => void) => {
    const handler = () => callback()
    ipcRenderer.on('recording:start', handler)
    return () => ipcRenderer.removeListener('recording:start', handler)
  },
  
  onRecordingComplete: (callback: (result: unknown) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, result: unknown) => callback(result)
    ipcRenderer.on('recording:complete', handler)
    return () => ipcRenderer.removeListener('recording:complete', handler)
  },
  
  onRecordingProcessing: (callback: () => void) => {
    const handler = () => callback()
    ipcRenderer.on('recording:processing', handler)
    return () => ipcRenderer.removeListener('recording:processing', handler)
  },
  
  onRecordingError: (callback: (error: string) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, error: string) => callback(error)
    ipcRenderer.on('recording:error', handler)
    return () => ipcRenderer.removeListener('recording:error', handler)
  },
  
  onRecordingLocked: (callback: () => void) => {
    const handler = () => callback()
    ipcRenderer.on('recording:locked', handler)
    return () => ipcRenderer.removeListener('recording:locked', handler)
  },
  
  getRecordingStatus: () => ipcRenderer.invoke('recording:status')
}

// Expose APIs to renderer
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error('Failed to expose APIs:', error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}

// Type definitions for renderer
export type API = typeof api
