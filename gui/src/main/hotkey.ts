import { globalShortcut } from 'electron'
import { uIOhook, UiohookKey } from 'uiohook-napi'
import { showRecordingIndicator, hideRecordingIndicator } from './windows'
import { setTrayRecording } from './tray'
import { sendToRenderer } from './ipc-handlers'

let currentHotkey: string | null = null
let currentMode: 'toggle' | 'push-to-talk' = 'toggle'
let isRecordingActive = false
let isProcessing = false // Lock to prevent concurrent operations
let lastHotkeyTime = 0
const DEBOUNCE_MS = 500 // Increased from 300 for better race condition prevention

// Track modifier + key states for push-to-talk
let pttActiveKeys = new Set<number>()
let pttRequiredKeys: number[] = []
let uiohookStarted = false

// Electron accelerator format -> uiohook key codes
const keyCodeMap: Record<string, number> = {
  'commandorcontrol': UiohookKey.Ctrl,
  'control': UiohookKey.Ctrl,
  'ctrl': UiohookKey.Ctrl,
  'alt': UiohookKey.Alt,
  'shift': UiohookKey.Shift,
  'command': UiohookKey.Meta,
  'meta': UiohookKey.Meta,
  'space': UiohookKey.Space,
  'return': UiohookKey.Enter,
  'enter': UiohookKey.Enter,
  'escape': UiohookKey.Escape,
  'tab': UiohookKey.Tab,
  'backspace': UiohookKey.Backspace,
  'delete': UiohookKey.Delete,
  'up': UiohookKey.ArrowUp,
  'down': UiohookKey.ArrowDown,
  'left': UiohookKey.ArrowLeft,
  'right': UiohookKey.ArrowRight,
  'a': UiohookKey.A, 'b': UiohookKey.B, 'c': UiohookKey.C, 'd': UiohookKey.D,
  'e': UiohookKey.E, 'f': UiohookKey.F, 'g': UiohookKey.G, 'h': UiohookKey.H,
  'i': UiohookKey.I, 'j': UiohookKey.J, 'k': UiohookKey.K, 'l': UiohookKey.L,
  'm': UiohookKey.M, 'n': UiohookKey.N, 'o': UiohookKey.O, 'p': UiohookKey.P,
  'q': UiohookKey.Q, 'r': UiohookKey.R, 's': UiohookKey.S, 't': UiohookKey.T,
  'u': UiohookKey.U, 'v': UiohookKey.V, 'w': UiohookKey.W, 'x': UiohookKey.X,
  'y': UiohookKey.Y, 'z': UiohookKey.Z,
  '0': UiohookKey.Num0, '1': UiohookKey.Num1, '2': UiohookKey.Num2, '3': UiohookKey.Num3,
  '4': UiohookKey.Num4, '5': UiohookKey.Num5, '6': UiohookKey.Num6, '7': UiohookKey.Num7,
  '8': UiohookKey.Num8, '9': UiohookKey.Num9,
  'f1': UiohookKey.F1, 'f2': UiohookKey.F2, 'f3': UiohookKey.F3, 'f4': UiohookKey.F4,
  'f5': UiohookKey.F5, 'f6': UiohookKey.F6, 'f7': UiohookKey.F7, 'f8': UiohookKey.F8,
  'f9': UiohookKey.F9, 'f10': UiohookKey.F10, 'f11': UiohookKey.F11, 'f12': UiohookKey.F12
}

function parseHotkeyToKeycodes(hotkey: string): number[] {
  return hotkey
    .toLowerCase()
    .split('+')
    .map(k => k.trim())
    .map(k => {
      if (k === 'ctrl' || k === 'control') return UiohookKey.Ctrl
      return keyCodeMap[k] ?? 0
    })
    .filter(k => k !== 0)
}

function normalizeHotkey(hotkey: string): string {
  return hotkey
    .split('+')
    .map(part => {
      const lower = part.toLowerCase().trim()
      switch (lower) {
        case 'ctrl':
        case 'control':
          return 'CommandOrControl'
        case 'cmd':
        case 'command':
          return 'Command'
        case 'alt':
          return 'Alt'
        case 'shift':
          return 'Shift'
        case 'space':
          return 'Space'
        case 'enter':
        case 'return':
          return 'Return'
        case 'esc':
        case 'escape':
          return 'Escape'
        case 'tab':
          return 'Tab'
        case 'backspace':
          return 'Backspace'
        case 'delete':
          return 'Delete'
        case 'up':
          return 'Up'
        case 'down':
          return 'Down'
        case 'left':
          return 'Left'
        case 'right':
          return 'Right'
        default:
          if (lower.length === 1) return lower.toUpperCase()
          if (lower.match(/^f\d+$/)) return lower.toUpperCase()
          return part
      }
    })
    .join('+')
}

async function startRecording(): Promise<void> {
  if (isRecordingActive || isProcessing) return
  
  isProcessing = true
  try {
    isRecordingActive = true
    console.log('Starting recording')
    
    setTrayRecording(true)
    showRecordingIndicator()
    sendToRenderer('recording:start')
    
    const response = await fetch('http://127.0.0.1:8765/api/transcribe/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    
    if (!response.ok) throw new Error(`Backend returned ${response.status}`)
  } catch (error) {
    console.error('Failed to start recording:', error)
    isRecordingActive = false
    setTrayRecording(false)
    hideRecordingIndicator()
    sendToRenderer('recording:error', String(error))
  } finally {
    isProcessing = false
  }
}

async function stopRecording(): Promise<void> {
  if (!isRecordingActive || isProcessing) return
  
  isProcessing = true
  try {
    isRecordingActive = false
    console.log('Stopping recording')
    
    setTrayRecording(false)
    hideRecordingIndicator()
    
    const response = await fetch('http://127.0.0.1:8765/api/transcribe/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ auto_paste: true })
    })
    
    if (!response.ok) throw new Error(`Backend returned ${response.status}`)
    
    const result = await response.json()
    console.log('Transcription result:', result.text?.substring(0, 50))
    sendToRenderer('recording:complete', result)
  } catch (error) {
    console.error('Failed to stop recording:', error)
    sendToRenderer('recording:error', String(error))
  } finally {
    isProcessing = false
  }
}

function allPttKeysPressed(): boolean {
  return pttRequiredKeys.every(k => pttActiveKeys.has(k))
}

function setupPushToTalk(hotkey: string): void {
  pttRequiredKeys = parseHotkeyToKeycodes(hotkey)
  pttActiveKeys.clear()
  
  if (pttRequiredKeys.length === 0) {
    console.error('Could not parse hotkey for push-to-talk:', hotkey)
    return
  }
  
  console.log(`Setting up push-to-talk with keys:`, pttRequiredKeys)
  
  uIOhook.on('keydown', (e) => {
    pttActiveKeys.add(e.keycode)
    
    if (!isRecordingActive && !isProcessing && allPttKeysPressed()) {
      const now = Date.now()
      if (now - lastHotkeyTime < DEBOUNCE_MS) return
      lastHotkeyTime = now
      startRecording()
    }
  })
  
  uIOhook.on('keyup', (e) => {
    pttActiveKeys.delete(e.keycode)
    
    if (isRecordingActive && !isProcessing && !allPttKeysPressed()) {
      stopRecording()
    }
  })
  
  if (!uiohookStarted) {
    uIOhook.start()
    uiohookStarted = true
  }
}

function setupToggleMode(hotkey: string): void {
   const accelerator = normalizeHotkey(hotkey)
   console.log(`Registering toggle hotkey: ${hotkey} -> ${accelerator}`)
   
   const success = globalShortcut.register(accelerator, () => {
     if (isProcessing) return
     
     const now = Date.now()
     if (now - lastHotkeyTime < DEBOUNCE_MS) return
     lastHotkeyTime = now
     
     if (isRecordingActive) {
       stopRecording()
     } else {
       startRecording()
     }
   })
  
  if (success) {
    console.log(`Toggle hotkey registered: ${accelerator}`)
  } else {
    throw new Error(`Failed to register hotkey: ${accelerator}`)
  }
}

export function registerGlobalHotkey(hotkey: string, mode: 'toggle' | 'push-to-talk' = 'toggle'): void {
  unregisterGlobalHotkey()
  
  currentHotkey = hotkey
  currentMode = mode
  
  if (mode === 'push-to-talk') {
    setupPushToTalk(hotkey)
  } else {
    setupToggleMode(hotkey)
  }
}

export function unregisterGlobalHotkey(): void {
  if (currentHotkey && currentMode === 'toggle') {
    const accelerator = normalizeHotkey(currentHotkey)
    globalShortcut.unregister(accelerator)
    console.log(`Toggle hotkey unregistered: ${accelerator}`)
  }
  
  if (uiohookStarted) {
    uIOhook.removeAllListeners()
    pttActiveKeys.clear()
  }
  
  currentHotkey = null
}

export function stopUiohook(): void {
  if (uiohookStarted) {
    uIOhook.stop()
    uiohookStarted = false
  }
}

export function getCurrentHotkey(): string | null {
  return currentHotkey
}

export function getHotkeyMode(): 'toggle' | 'push-to-talk' {
  return currentMode
}

export function isRecording(): boolean {
  return isRecordingActive
}
