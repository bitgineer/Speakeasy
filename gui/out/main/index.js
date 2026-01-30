"use strict";
const electron = require("electron");
const utils = require("@electron-toolkit/utils");
const path = require("path");
const child_process = require("child_process");
const fs = require("fs");
const uiohookNapi = require("uiohook-napi");
let trackingInterval = null;
let currentDisplayId = null;
function startOverlayTracking(window) {
  stopOverlayTracking();
  updatePosition(window);
  trackingInterval = setInterval(() => {
    if (window.isDestroyed()) {
      stopOverlayTracking();
      return;
    }
    const cursor = electron.screen.getCursorScreenPoint();
    const display = electron.screen.getDisplayNearestPoint(cursor);
    if (display.id !== currentDisplayId) {
      updatePosition(window);
    }
  }, 100);
}
function stopOverlayTracking() {
  if (trackingInterval) {
    clearInterval(trackingInterval);
    trackingInterval = null;
  }
}
function updatePosition(window, width, height) {
  if (window.isDestroyed()) return;
  const cursor = electron.screen.getCursorScreenPoint();
  const display = electron.screen.getDisplayNearestPoint(cursor);
  currentDisplayId = display.id;
  const workArea = display.workArea;
  const bounds = window.getBounds();
  const targetWidth = width || bounds.width;
  const targetHeight = height || bounds.height;
  const bottomMargin = 20;
  const x = Math.round(workArea.x + workArea.width / 2 - targetWidth / 2);
  const y = Math.round(workArea.y + workArea.height - targetHeight - bottomMargin);
  window.setBounds({
    x,
    y,
    width: targetWidth,
    height: targetHeight
  });
}
let mainWindow = null;
let recordingIndicator = null;
function createMainWindow() {
  mainWindow = new electron.BrowserWindow({
    width: 900,
    height: 670,
    minWidth: 600,
    minHeight: 400,
    show: false,
    autoHideMenuBar: true,
    frame: true,
    titleBarStyle: "hiddenInset",
    backgroundColor: "#18181b",
    // surface-900
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  mainWindow.on("ready-to-show", () => {
    mainWindow?.show();
  });
  mainWindow.webContents.setWindowOpenHandler((details) => {
    electron.shell.openExternal(details.url);
    return { action: "deny" };
  });
  if (utils.is.dev && process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
  mainWindow.on("close", (event) => {
    if (!mainWindow?.isDestroyed()) {
      event.preventDefault();
      mainWindow?.hide();
    }
  });
  return mainWindow;
}
function createRecordingIndicator() {
  const { width: screenWidth, height: screenHeight } = electron.screen.getPrimaryDisplay().workAreaSize;
  const indicatorWidth = 800;
  const indicatorHeight = 200;
  const bottomMargin = 50;
  recordingIndicator = new electron.BrowserWindow({
    width: indicatorWidth,
    height: indicatorHeight,
    x: Math.round(screenWidth / 2 - indicatorWidth / 2),
    y: screenHeight - indicatorHeight - bottomMargin,
    show: true,
    // Show immediately on startup (Always On)
    frame: false,
    transparent: true,
    backgroundColor: "#00000000",
    // Restore this to fix visibility
    alwaysOnTop: true,
    skipTaskbar: true,
    type: "toolbar",
    // Hint to OS that this is a toolbar/overlay
    resizable: false,
    movable: false,
    focusable: false,
    hasShadow: false,
    // Shadow handled in CSS
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  recordingIndicator.setIgnoreMouseEvents(true, { forward: true });
  startOverlayTracking(recordingIndicator);
  recordingIndicator.on("closed", () => {
    stopOverlayTracking();
    recordingIndicator = null;
  });
  if (utils.is.dev && process.env["ELECTRON_RENDERER_URL"]) {
    recordingIndicator.loadURL(`${process.env["ELECTRON_RENDERER_URL"]}#/recording-indicator`);
  } else {
    recordingIndicator.loadFile(path.join(__dirname, "../renderer/index.html"), {
      hash: "/recording-indicator"
    });
  }
  return recordingIndicator;
}
function showRecordingIndicator() {
  if (recordingIndicator && !recordingIndicator.isDestroyed()) {
    recordingIndicator.setAlwaysOnTop(true, "screen-saver");
    recordingIndicator.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    recordingIndicator.show();
    recordingIndicator.setSkipTaskbar(true);
    updatePosition(recordingIndicator);
  }
}
function resizeRecordingIndicator(width, height) {
  if (recordingIndicator && !recordingIndicator.isDestroyed()) {
    updatePosition(recordingIndicator, width, height);
  }
}
function hideRecordingIndicator() {
  if (recordingIndicator && !recordingIndicator.isDestroyed()) {
    recordingIndicator.hide();
  }
}
function getMainWindow() {
  return mainWindow;
}
function getRecordingIndicator() {
  return recordingIndicator;
}
function showMainWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show();
    mainWindow.focus();
  } else {
    createMainWindow();
  }
}
function hideMainWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.hide();
  }
}
let tray = null;
let isRecording$1 = false;
function createTrayIcon(recording) {
  const size = 32;
  const canvas = Buffer.alloc(size * size * 4);
  const bgColor = recording ? { r: 239, g: 68, b: 68 } : { r: 14, g: 165, b: 233 };
  const center = size / 2;
  const outerRadius = 14;
  const innerRadius = recording ? 6 : 8;
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (y * size + x) * 4;
      const dist = Math.sqrt((x - center) ** 2 + (y - center) ** 2);
      const inShape = recording ? dist <= outerRadius : dist <= outerRadius && dist >= innerRadius;
      if (inShape) {
        let alpha = 255;
        if (dist > outerRadius - 1) {
          alpha = Math.max(0, outerRadius - dist) * 255;
        } else if (!recording && dist < innerRadius + 1) {
          alpha = Math.max(0, dist - innerRadius) * 255;
        }
        canvas[idx] = bgColor.r;
        canvas[idx + 1] = bgColor.g;
        canvas[idx + 2] = bgColor.b;
        canvas[idx + 3] = Math.round(alpha);
      }
    }
  }
  return electron.nativeImage.createFromBuffer(canvas, { width: size, height: size });
}
function loadTrayIcon(recording) {
  return createTrayIcon(recording);
}
function buildContextMenu() {
  return electron.Menu.buildFromTemplate([
    {
      label: isRecording$1 ? "Recording..." : "Ready",
      enabled: false,
      icon: loadTrayIcon(isRecording$1).resize({ width: 16, height: 16 })
    },
    { type: "separator" },
    {
      label: "Open Dashboard",
      click: () => showMainWindow()
    },
    {
      label: "Settings",
      click: () => {
        showMainWindow();
        const { BrowserWindow } = require("electron");
        const mainWindow2 = BrowserWindow.getAllWindows()[0];
        if (mainWindow2) {
          mainWindow2.webContents.send("navigate", "/settings");
        }
      }
    },
    { type: "separator" },
    {
      label: "Quit SpeakEasy",
      click: () => electron.app.quit()
    }
  ]);
}
function createTray() {
  const icon = loadTrayIcon(false);
  tray = new electron.Tray(icon);
  tray.setToolTip("SpeakEasy - Voice Transcription");
  tray.setContextMenu(buildContextMenu());
  tray.on("click", () => {
    showMainWindow();
  });
  return tray;
}
function setTrayRecording(recording) {
  isRecording$1 = recording;
  if (tray && !tray.isDestroyed()) {
    tray.setImage(loadTrayIcon(recording));
    tray.setToolTip(recording ? "SpeakEasy - Recording..." : "SpeakEasy - Ready");
    tray.setContextMenu(buildContextMenu());
  }
}
function destroyTray() {
  if (tray && !tray.isDestroyed()) {
    tray.destroy();
    tray = null;
  }
}
let backendProcess = null;
let backendPort = 8765;
const BACKEND_STARTUP_TIMEOUT = 12e4;
const isWin = process.platform === "win32";
const pythonExec = isWin ? "python.exe" : "python3";
function getPythonPath() {
  const rootDir = electron.app.isPackaged ? process.resourcesPath : path.join(electron.app.getAppPath(), "../");
  const venvPython = isWin ? path.join(rootDir, ".venv", "Scripts", "python.exe") : path.join(rootDir, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) {
    console.log(`[Backend] Using venv python: ${venvPython}`);
    return venvPython;
  }
  console.log(`[Backend] Venv not found at ${venvPython}, using system python: ${pythonExec}`);
  return pythonExec;
}
function getBackendPath() {
  return electron.app.isPackaged ? path.join(process.resourcesPath, "backend") : path.join(electron.app.getAppPath(), "../backend");
}
async function checkBackendHealth() {
  return new Promise((resolve) => {
    const request = electron.net.request(`http://127.0.0.1:${backendPort}/api/health`);
    request.on("response", (response) => {
      resolve(response.statusCode === 200);
    });
    request.on("error", () => {
      resolve(false);
    });
    request.end();
  });
}
async function waitForBackend(timeoutMs = BACKEND_STARTUP_TIMEOUT) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    if (await checkBackendHealth()) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return false;
}
async function startBackend() {
  if (await checkBackendHealth()) {
    console.log("Backend already running");
    return;
  }
  const pythonPath = getPythonPath();
  const backendPath = getBackendPath();
  console.log(`Starting backend: ${pythonPath} -m speakeasy --port ${backendPort}`);
  console.log(`Backend path: ${backendPath}`);
  try {
    backendProcess = child_process.spawn(pythonPath, ["-m", "speakeasy", "--port", String(backendPort)], {
      cwd: backendPath,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1"
      },
      stdio: ["ignore", "pipe", "pipe"]
    });
    backendProcess.stdout?.on("data", (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });
    backendProcess.stderr?.on("data", (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });
    backendProcess.on("exit", (code, signal) => {
      console.log(`Backend process exited with code ${code}, signal ${signal}`);
      backendProcess = null;
    });
    backendProcess.on("error", (error) => {
      console.error("Failed to start backend process:", error);
      backendProcess = null;
    });
    const isHealthy = await waitForBackend();
    if (!isHealthy) {
      throw new Error("Backend failed to start within timeout");
    }
    console.log("Backend started and healthy");
  } catch (error) {
    console.error("Error starting backend:", error);
    throw error;
  }
}
async function stopBackend() {
  if (!backendProcess) {
    return;
  }
  console.log("Stopping backend process...");
  return new Promise((resolve) => {
    if (!backendProcess) {
      resolve();
      return;
    }
    const timeout = setTimeout(() => {
      if (backendProcess) {
        console.log("Force killing backend process");
        backendProcess.kill("SIGKILL");
      }
      resolve();
    }, 5e3);
    backendProcess.on("exit", () => {
      clearTimeout(timeout);
      backendProcess = null;
      resolve();
    });
    backendProcess.kill("SIGTERM");
  });
}
function isBackendRunning() {
  return backendProcess !== null && !backendProcess.killed;
}
function getBackendPort() {
  return backendPort;
}
let currentHotkey = null;
let currentMode = "toggle";
let isRecordingActive = false;
let isProcessing = false;
let lastHotkeyTime = 0;
const DEBOUNCE_MS = 500;
const LOCK_THRESHOLD_MS = 6e4;
let lockTimer = null;
let isLocked = false;
let lastPttState = false;
let pttActiveKeys = /* @__PURE__ */ new Set();
let pttRequiredKeys = [];
let uiohookStarted = false;
const keyCodeMap = {
  "commandorcontrol": uiohookNapi.UiohookKey.Ctrl,
  "control": uiohookNapi.UiohookKey.Ctrl,
  "ctrl": uiohookNapi.UiohookKey.Ctrl,
  "alt": uiohookNapi.UiohookKey.Alt,
  "shift": uiohookNapi.UiohookKey.Shift,
  "command": uiohookNapi.UiohookKey.Meta,
  "meta": uiohookNapi.UiohookKey.Meta,
  "space": uiohookNapi.UiohookKey.Space,
  "return": uiohookNapi.UiohookKey.Enter,
  "enter": uiohookNapi.UiohookKey.Enter,
  "escape": uiohookNapi.UiohookKey.Escape,
  "tab": uiohookNapi.UiohookKey.Tab,
  "backspace": uiohookNapi.UiohookKey.Backspace,
  "delete": uiohookNapi.UiohookKey.Delete,
  "up": uiohookNapi.UiohookKey.ArrowUp,
  "down": uiohookNapi.UiohookKey.ArrowDown,
  "left": uiohookNapi.UiohookKey.ArrowLeft,
  "right": uiohookNapi.UiohookKey.ArrowRight,
  "a": uiohookNapi.UiohookKey.A,
  "b": uiohookNapi.UiohookKey.B,
  "c": uiohookNapi.UiohookKey.C,
  "d": uiohookNapi.UiohookKey.D,
  "e": uiohookNapi.UiohookKey.E,
  "f": uiohookNapi.UiohookKey.F,
  "g": uiohookNapi.UiohookKey.G,
  "h": uiohookNapi.UiohookKey.H,
  "i": uiohookNapi.UiohookKey.I,
  "j": uiohookNapi.UiohookKey.J,
  "k": uiohookNapi.UiohookKey.K,
  "l": uiohookNapi.UiohookKey.L,
  "m": uiohookNapi.UiohookKey.M,
  "n": uiohookNapi.UiohookKey.N,
  "o": uiohookNapi.UiohookKey.O,
  "p": uiohookNapi.UiohookKey.P,
  "q": uiohookNapi.UiohookKey.Q,
  "r": uiohookNapi.UiohookKey.R,
  "s": uiohookNapi.UiohookKey.S,
  "t": uiohookNapi.UiohookKey.T,
  "u": uiohookNapi.UiohookKey.U,
  "v": uiohookNapi.UiohookKey.V,
  "w": uiohookNapi.UiohookKey.W,
  "x": uiohookNapi.UiohookKey.X,
  "y": uiohookNapi.UiohookKey.Y,
  "z": uiohookNapi.UiohookKey.Z,
  "0": uiohookNapi.UiohookKey.Num0,
  "1": uiohookNapi.UiohookKey.Num1,
  "2": uiohookNapi.UiohookKey.Num2,
  "3": uiohookNapi.UiohookKey.Num3,
  "4": uiohookNapi.UiohookKey.Num4,
  "5": uiohookNapi.UiohookKey.Num5,
  "6": uiohookNapi.UiohookKey.Num6,
  "7": uiohookNapi.UiohookKey.Num7,
  "8": uiohookNapi.UiohookKey.Num8,
  "9": uiohookNapi.UiohookKey.Num9,
  "f1": uiohookNapi.UiohookKey.F1,
  "f2": uiohookNapi.UiohookKey.F2,
  "f3": uiohookNapi.UiohookKey.F3,
  "f4": uiohookNapi.UiohookKey.F4,
  "f5": uiohookNapi.UiohookKey.F5,
  "f6": uiohookNapi.UiohookKey.F6,
  "f7": uiohookNapi.UiohookKey.F7,
  "f8": uiohookNapi.UiohookKey.F8,
  "f9": uiohookNapi.UiohookKey.F9,
  "f10": uiohookNapi.UiohookKey.F10,
  "f11": uiohookNapi.UiohookKey.F11,
  "f12": uiohookNapi.UiohookKey.F12
};
function parseHotkeyToKeycodes(hotkey) {
  return hotkey.toLowerCase().split("+").map((k) => k.trim()).map((k) => {
    if (k === "ctrl" || k === "control") return uiohookNapi.UiohookKey.Ctrl;
    return keyCodeMap[k] ?? 0;
  }).filter((k) => k !== 0);
}
function normalizeHotkey(hotkey) {
  return hotkey.split("+").map((part) => {
    const lower = part.toLowerCase().trim();
    switch (lower) {
      case "ctrl":
      case "control":
        return "CommandOrControl";
      case "cmd":
      case "command":
        return "Command";
      case "alt":
        return "Alt";
      case "shift":
        return "Shift";
      case "space":
        return "Space";
      case "enter":
      case "return":
        return "Return";
      case "esc":
      case "escape":
        return "Escape";
      case "tab":
        return "Tab";
      case "backspace":
        return "Backspace";
      case "delete":
        return "Delete";
      case "up":
        return "Up";
      case "down":
        return "Down";
      case "left":
        return "Left";
      case "right":
        return "Right";
      default:
        if (lower.length === 1) return lower.toUpperCase();
        if (lower.match(/^f\d+$/)) return lower.toUpperCase();
        return part;
    }
  }).join("+");
}
async function startRecording() {
  if (isRecordingActive || isProcessing) return;
  isProcessing = true;
  try {
    isRecordingActive = true;
    isLocked = false;
    console.log("Starting recording");
    if (currentMode === "push-to-talk") {
      if (lockTimer) clearTimeout(lockTimer);
      lockTimer = setTimeout(() => {
        if (isRecordingActive) {
          isLocked = true;
          console.log("Recording locked (long press)");
          sendToRenderer("recording:locked");
        }
      }, LOCK_THRESHOLD_MS);
    }
    setTrayRecording(true);
    showRecordingIndicator();
    sendToRenderer("recording:start");
    const response = await fetch("http://127.0.0.1:8765/api/transcribe/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  } catch (error) {
    console.error("Failed to start recording:", error);
    isRecordingActive = false;
    setTrayRecording(false);
    hideRecordingIndicator();
    sendToRenderer("recording:error", String(error));
  } finally {
    isProcessing = false;
  }
}
async function stopRecording() {
  if (!isRecordingActive || isProcessing) return;
  if (lockTimer) {
    clearTimeout(lockTimer);
    lockTimer = null;
  }
  isLocked = false;
  isProcessing = true;
  try {
    isRecordingActive = false;
    console.log("Stopping recording");
    setTrayRecording(false);
    sendToRenderer("recording:processing");
    const response = await fetch("http://127.0.0.1:8765/api/transcribe/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ auto_paste: true })
    });
    if (!response.ok) throw new Error(`Backend returned ${response.status}`);
    const result = await response.json();
    console.log("Transcription result:", result.text?.substring(0, 50));
    sendToRenderer("recording:complete", result);
  } catch (error) {
    console.error("Failed to stop recording:", error);
    sendToRenderer("recording:error", String(error));
  } finally {
    isProcessing = false;
  }
}
async function cancelRecording() {
  if (!isRecordingActive || isProcessing) return;
  if (lockTimer) {
    clearTimeout(lockTimer);
    lockTimer = null;
  }
  isLocked = false;
  isProcessing = true;
  try {
    isRecordingActive = false;
    console.log("Cancelling recording");
    setTrayRecording(false);
    const response = await fetch("http://127.0.0.1:8765/api/transcribe/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    if (!response.ok) throw new Error(`Backend returned ${response.status}`);
    sendToRenderer("recording:error", "Cancelled by user");
  } catch (error) {
    console.error("Failed to cancel recording:", error);
    sendToRenderer("recording:error", String(error));
  } finally {
    isProcessing = false;
  }
}
function allPttKeysPressed() {
  return pttRequiredKeys.every((k) => pttActiveKeys.has(k));
}
function setupPushToTalk(hotkey) {
  uiohookNapi.uIOhook.removeAllListeners("keydown");
  uiohookNapi.uIOhook.removeAllListeners("keyup");
  pttRequiredKeys = parseHotkeyToKeycodes(hotkey);
  pttActiveKeys.clear();
  lastPttState = false;
  if (pttRequiredKeys.length === 0) {
    console.error("Could not parse hotkey for push-to-talk:", hotkey);
    return;
  }
  console.log(`Setting up push-to-talk with keys:`, pttRequiredKeys);
  uiohookNapi.uIOhook.on("keydown", (e) => {
    pttActiveKeys.add(e.keycode);
    const currentState = allPttKeysPressed();
    if (currentState && !lastPttState) {
      if (!isRecordingActive && !isProcessing) {
        const now = Date.now();
        if (now - lastHotkeyTime < DEBOUNCE_MS) return;
        lastHotkeyTime = now;
        startRecording();
      } else if (isRecordingActive && isLocked && !isProcessing) {
        const now = Date.now();
        if (now - lastHotkeyTime < DEBOUNCE_MS) return;
        lastHotkeyTime = now;
        stopRecording();
      }
    }
    lastPttState = currentState;
  });
  uiohookNapi.uIOhook.on("keyup", (e) => {
    pttActiveKeys.delete(e.keycode);
    const currentState = allPttKeysPressed();
    if (!currentState && lastPttState) {
      if (isRecordingActive && !isLocked && !isProcessing) {
        stopRecording();
      }
    }
    lastPttState = currentState;
  });
  if (!uiohookStarted) {
    uiohookNapi.uIOhook.start();
    uiohookStarted = true;
  }
}
function setupToggleMode(hotkey) {
  const accelerator = normalizeHotkey(hotkey);
  console.log(`Registering toggle hotkey: ${hotkey} -> ${accelerator}`);
  const success = electron.globalShortcut.register(accelerator, () => {
    if (isProcessing) return;
    const now = Date.now();
    if (now - lastHotkeyTime < DEBOUNCE_MS) return;
    lastHotkeyTime = now;
    if (isRecordingActive) {
      stopRecording();
    } else {
      startRecording();
    }
  });
  if (success) {
    console.log(`Toggle hotkey registered: ${accelerator}`);
  } else {
    throw new Error(`Failed to register hotkey: ${accelerator}`);
  }
}
function registerGlobalHotkey(hotkey, mode = "toggle") {
  unregisterGlobalHotkey();
  currentHotkey = hotkey;
  currentMode = mode;
  if (mode === "push-to-talk") {
    setupPushToTalk(hotkey);
  } else {
    setupToggleMode(hotkey);
  }
}
function unregisterGlobalHotkey() {
  if (currentHotkey && currentMode === "toggle") {
    const accelerator = normalizeHotkey(currentHotkey);
    electron.globalShortcut.unregister(accelerator);
    console.log(`Toggle hotkey unregistered: ${accelerator}`);
  }
  if (uiohookStarted) {
    uiohookNapi.uIOhook.removeAllListeners();
    pttActiveKeys.clear();
  }
  currentHotkey = null;
}
function stopUiohook() {
  if (uiohookStarted) {
    uiohookNapi.uIOhook.stop();
    uiohookStarted = false;
  }
}
function getCurrentHotkey() {
  return currentHotkey;
}
function getHotkeyMode() {
  return currentMode;
}
function isRecording() {
  return isRecordingActive;
}
function setupIpcHandlers() {
  electron.ipcMain.handle("window:show", () => {
    showMainWindow();
  });
  electron.ipcMain.handle("window:hide", () => {
    hideMainWindow();
  });
  electron.ipcMain.handle("recording:start", async () => {
    await startRecording();
  });
  electron.ipcMain.handle("recording:stop", async () => {
    await stopRecording();
  });
  electron.ipcMain.handle("recording:cancel", async () => {
    await cancelRecording();
  });
  electron.ipcMain.handle("recording:status", () => {
    return isRecording();
  });
  electron.ipcMain.handle("indicator:show", () => {
    showRecordingIndicator();
  });
  electron.ipcMain.handle("indicator:hide", () => {
    hideRecordingIndicator();
  });
  electron.ipcMain.handle("indicator:resize", (_, width, height) => {
    resizeRecordingIndicator(width, height);
  });
  electron.ipcMain.handle("indicator:setIgnoreMouseEvents", (_, ignore, options) => {
    const indicator = getRecordingIndicator();
    if (indicator && !indicator.isDestroyed()) {
      indicator.setIgnoreMouseEvents(ignore, options);
    }
  });
  electron.ipcMain.handle("backend:status", () => {
    return {
      running: isBackendRunning(),
      port: getBackendPort()
    };
  });
  electron.ipcMain.handle("backend:port", () => {
    return getBackendPort();
  });
  electron.ipcMain.handle("hotkey:register", async (_, hotkey, mode = "toggle") => {
    try {
      registerGlobalHotkey(hotkey, mode);
      return { success: true };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  });
  electron.ipcMain.handle("hotkey:unregister", () => {
    unregisterGlobalHotkey();
    return { success: true };
  });
  electron.ipcMain.handle("hotkey:current", () => {
    return { hotkey: getCurrentHotkey(), mode: getHotkeyMode() };
  });
  electron.ipcMain.handle("app:version", () => {
    return electron.app.getVersion();
  });
  electron.ipcMain.handle("app:quit", () => {
    electron.app.quit();
  });
  electron.ipcMain.handle("dialog:showError", async (_, title, content) => {
    await electron.dialog.showErrorBox(title, content);
  });
  electron.ipcMain.handle("dialog:showMessage", async (_, options) => {
    return electron.dialog.showMessageBox(options);
  });
}
function sendToRenderer(channel, ...args) {
  const { BrowserWindow } = require("electron");
  BrowserWindow.getAllWindows().forEach((window) => {
    if (!window.isDestroyed()) {
      window.webContents.send(channel, ...args);
    }
  });
}
const gotTheLock = electron.app.requestSingleInstanceLock();
if (!gotTheLock) {
  electron.app.quit();
} else {
  electron.app.on("second-instance", () => {
    const mainWindow2 = getMainWindow();
    if (mainWindow2) {
      if (mainWindow2.isMinimized()) mainWindow2.restore();
      mainWindow2.focus();
    }
  });
  electron.app.whenReady().then(async () => {
    utils.electronApp.setAppUserModelId("com.speakeasy.app");
    electron.app.on("browser-window-created", (_, window) => {
      utils.optimizer.watchWindowShortcuts(window);
    });
    setupIpcHandlers();
    try {
      await startBackend();
      console.log("Backend started successfully");
    } catch (error) {
      console.error("Failed to start backend:", error);
    }
    createMainWindow();
    createRecordingIndicator();
    showRecordingIndicator();
    createTray();
    electron.app.on("activate", () => {
      if (electron.BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
      }
    });
  });
  electron.app.on("before-quit", async () => {
    console.log("[BEFORE-QUIT] Starting shutdown sequence...");
    console.log("[BEFORE-QUIT] Unregistering global hotkey...");
    unregisterGlobalHotkey();
    console.log("[BEFORE-QUIT] Hotkey unregistered. Stopping uiohook...");
    stopUiohook();
    console.log("[BEFORE-QUIT] Uiohook stopped. Stopping backend...");
    await stopBackend();
    console.log("[BEFORE-QUIT] Backend stopped. Destroying tray...");
    destroyTray();
    console.log("[BEFORE-QUIT] Shutdown complete!");
  });
  electron.app.on("window-all-closed", () => {
    if (process.platform !== "darwin") ;
  });
}
