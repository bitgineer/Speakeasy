import { Tray, Menu, nativeImage, app } from 'electron'
import { showMainWindow, getMainWindow } from './windows'

let tray: Tray | null = null
let isRecording = false

// Windows tray doesn't support SVG - generate RGBA buffer directly
function createTrayIcon(recording: boolean): Electron.NativeImage {
  const size = 32
  const canvas = Buffer.alloc(size * size * 4)
  
  const bgColor = recording 
    ? { r: 239, g: 68, b: 68, a: 255 }
    : { r: 14, g: 165, b: 233, a: 255 }
  
  const center = size / 2
  const outerRadius = 14
  const innerRadius = recording ? 6 : 8
  
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (y * size + x) * 4
      const dist = Math.sqrt((x - center) ** 2 + (y - center) ** 2)
      
      const inShape = recording 
        ? dist <= outerRadius
        : dist <= outerRadius && dist >= innerRadius
      
      if (inShape) {
        // Anti-aliased edges
        let alpha = 255
        if (dist > outerRadius - 1) {
          alpha = Math.max(0, (outerRadius - dist)) * 255
        } else if (!recording && dist < innerRadius + 1) {
          alpha = Math.max(0, (dist - innerRadius)) * 255
        }
        canvas[idx] = bgColor.r
        canvas[idx + 1] = bgColor.g
        canvas[idx + 2] = bgColor.b
        canvas[idx + 3] = Math.round(alpha)
      }
    }
  }
  
  return nativeImage.createFromBuffer(canvas, { width: size, height: size })
}

function loadTrayIcon(recording: boolean): Electron.NativeImage {
  return createTrayIcon(recording)
}

function buildContextMenu(): Menu {
  return Menu.buildFromTemplate([
    {
      label: isRecording ? 'Recording...' : 'Ready',
      enabled: false,
      icon: loadTrayIcon(isRecording).resize({ width: 16, height: 16 })
    },
    { type: 'separator' },
    {
      label: 'Open Dashboard',
      click: () => showMainWindow()
    },
    {
      label: 'Settings',
      click: () => {
        showMainWindow()
        const mainWindow = getMainWindow()
        if (mainWindow) {
          mainWindow.webContents.send('navigate', '/settings')
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Quit SpeakEasy',
      click: () => app.quit()
    }
  ])
}

export function createTray(): Tray {
  const icon = loadTrayIcon(false)
  tray = new Tray(icon)
  
  tray.setToolTip('SpeakEasy - Voice Transcription')
  tray.setContextMenu(buildContextMenu())
  
  // Click to show/hide main window
  tray.on('click', () => {
    showMainWindow()
  })
  
  return tray
}

export function setTrayRecording(recording: boolean): void {
  isRecording = recording
  
  if (tray && !tray.isDestroyed()) {
    tray.setImage(loadTrayIcon(recording))
    tray.setToolTip(recording ? 'SpeakEasy - Recording...' : 'SpeakEasy - Ready')
    tray.setContextMenu(buildContextMenu())
  }
}

export function destroyTray(): void {
  if (tray && !tray.isDestroyed()) {
    tray.destroy()
    tray = null
  }
}

export function getTray(): Tray | null {
  return tray
}
