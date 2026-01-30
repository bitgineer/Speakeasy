"use strict";
const electron = require("electron");
const preload = require("@electron-toolkit/preload");
const api = {
  // Window controls
  showWindow: () => electron.ipcRenderer.invoke("window:show"),
  hideWindow: () => electron.ipcRenderer.invoke("window:hide"),
  // Recording indicator
  showIndicator: () => electron.ipcRenderer.invoke("indicator:show"),
  hideIndicator: () => electron.ipcRenderer.invoke("indicator:hide"),
  resizeIndicator: (width, height) => electron.ipcRenderer.invoke("indicator:resize", width, height),
  setIgnoreMouseEvents: (ignore, options) => electron.ipcRenderer.invoke("indicator:setIgnoreMouseEvents", ignore, options),
  startRecording: () => electron.ipcRenderer.invoke("recording:start"),
  stopRecording: () => electron.ipcRenderer.invoke("recording:stop"),
  cancelRecording: () => electron.ipcRenderer.invoke("recording:cancel"),
  // Backend
  getBackendStatus: () => electron.ipcRenderer.invoke("backend:status"),
  getBackendPort: () => electron.ipcRenderer.invoke("backend:port"),
  // Hotkey
  registerHotkey: (hotkey, mode = "toggle") => electron.ipcRenderer.invoke("hotkey:register", hotkey, mode),
  unregisterHotkey: () => electron.ipcRenderer.invoke("hotkey:unregister"),
  getCurrentHotkey: () => electron.ipcRenderer.invoke("hotkey:current"),
  // App
  getVersion: () => electron.ipcRenderer.invoke("app:version"),
  quit: () => electron.ipcRenderer.invoke("app:quit"),
  // Dialogs
  showError: (title, content) => electron.ipcRenderer.invoke("dialog:showError", title, content),
  showMessage: (options) => electron.ipcRenderer.invoke("dialog:showMessage", options),
  // Event listeners
  onNavigate: (callback) => {
    const handler = (_event, path) => callback(path);
    electron.ipcRenderer.on("navigate", handler);
    return () => electron.ipcRenderer.removeListener("navigate", handler);
  },
  onRecordingStart: (callback) => {
    const handler = () => callback();
    electron.ipcRenderer.on("recording:start", handler);
    return () => electron.ipcRenderer.removeListener("recording:start", handler);
  },
  onRecordingComplete: (callback) => {
    const handler = (_event, result) => callback(result);
    electron.ipcRenderer.on("recording:complete", handler);
    return () => electron.ipcRenderer.removeListener("recording:complete", handler);
  },
  onRecordingProcessing: (callback) => {
    const handler = () => callback();
    electron.ipcRenderer.on("recording:processing", handler);
    return () => electron.ipcRenderer.removeListener("recording:processing", handler);
  },
  onRecordingError: (callback) => {
    const handler = (_event, error) => callback(error);
    electron.ipcRenderer.on("recording:error", handler);
    return () => electron.ipcRenderer.removeListener("recording:error", handler);
  },
  onRecordingLocked: (callback) => {
    const handler = () => callback();
    electron.ipcRenderer.on("recording:locked", handler);
    return () => electron.ipcRenderer.removeListener("recording:locked", handler);
  },
  getRecordingStatus: () => electron.ipcRenderer.invoke("recording:status")
};
if (process.contextIsolated) {
  try {
    electron.contextBridge.exposeInMainWorld("electron", preload.electronAPI);
    electron.contextBridge.exposeInMainWorld("api", api);
  } catch (error) {
    console.error("Failed to expose APIs:", error);
  }
} else {
  window.electron = preload.electronAPI;
  window.api = api;
}
