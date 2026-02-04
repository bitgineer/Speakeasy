/**
 * Python Backend Process Management
 * 
 * Spawns and manages the Python FastAPI backend process.
 */

import { spawn, ChildProcess } from 'child_process'
import { join } from 'path'
import { app } from 'electron'
import { existsSync } from 'fs'
import { net } from 'electron'

let backendProcess: ChildProcess | null = null
let backendPort = 8765
const BACKEND_STARTUP_TIMEOUT = 120000 // 120 seconds for first-time model download

// Platform specific Python executable
const isWin = process.platform === 'win32'
const pythonExec = isWin ? 'python.exe' : 'python3'

// Find python executable or uv
function getPythonCommand(): { cmd: string, args: string[] } {
  // Check for venv in root project directory
  const rootDir = app.isPackaged 
    ? process.resourcesPath
    : join(app.getAppPath(), '../') // Go up from gui to SpeakEasy root

  // Check for UV first (only in dev/unpacked mode or if available in path)
  // We prefer UV if it's available and we see a uv.lock file
  const uvLockPath = join(rootDir, 'backend', 'uv.lock')
  
  // Simple check if 'uv' is in PATH. 
  // In a real app, we might want a more robust check (e.g. execSync('uv --version'))
  // but for now, we'll assume if they installed with our script, uv is in path.
  let uvAvailable = false
  try {
     const { execSync } = require('child_process')
     execSync('uv --version', { stdio: 'ignore' })
     uvAvailable = true
  } catch (e) {
     uvAvailable = false
  }

  if (uvAvailable && existsSync(uvLockPath)) {
      console.log('[Backend] Using uv to run backend')
      return { cmd: 'uv', args: ['run', '-m', 'speakeasy', '--port', String(backendPort)] }
  }
    
  const venvPython = isWin
    ? join(rootDir, '.venv', 'Scripts', 'python.exe')
    : join(rootDir, '.venv', 'bin', 'python')

  if (existsSync(venvPython)) {
    console.log(`[Backend] Using venv python: ${venvPython}`)
    return { cmd: venvPython, args: ['-m', 'speakeasy', '--port', String(backendPort)] }
  }
  
  // Fallback to system python
  console.log(`[Backend] Venv not found at ${venvPython}, using system python: ${pythonExec}`)
  return { cmd: pythonExec, args: ['-m', 'speakeasy', '--port', String(backendPort)] }
}

function getBackendPath(): string {
  // Path to backend module
  // In dev: app.getAppPath() is gui folder. Backend is ../backend
  // In prod: resources/backend
  return app.isPackaged
    ? join(process.resourcesPath, 'backend')
    : join(app.getAppPath(), '../backend')
}

/**
 * Check if backend is healthy
 */
async function checkBackendHealth(): Promise<boolean> {
  return new Promise((resolve) => {
    const request = net.request(`http://127.0.0.1:${backendPort}/api/health`)
    
    request.on('response', (response) => {
      resolve(response.statusCode === 200)
    })
    
    request.on('error', () => {
      resolve(false)
    })
    
    request.end()
  })
}

/**
 * Wait for the backend to become healthy
 */
async function waitForBackend(timeoutMs: number = BACKEND_STARTUP_TIMEOUT): Promise<boolean> {
  const startTime = Date.now()
  
  while (Date.now() - startTime < timeoutMs) {
    if (await checkBackendHealth()) {
      return true
    }
    await new Promise(resolve => setTimeout(resolve, 500))
  }
  
  return false
}

/**
 * Start the Python backend process
 */
export async function startBackend(): Promise<void> {
  // Check if backend is already running (maybe started externally in dev)
  if (await checkBackendHealth()) {
    console.log('Backend already running')
    return
  }
  
  const { cmd, args } = getPythonCommand()
  const backendPath = getBackendPath()
  
  console.log(`Starting backend: ${cmd} ${args.join(' ')}`)
  console.log(`Backend path: ${backendPath}`)
  
  try {
    backendProcess = spawn(cmd, args, {
      cwd: backendPath,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1'
      },
      stdio: ['ignore', 'pipe', 'pipe']
    })
    
    // Log stdout
    backendProcess.stdout?.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`)
    })
    
    // Log stderr
    backendProcess.stderr?.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`)
    })
    
    // Handle process exit
    backendProcess.on('exit', (code, signal) => {
      console.log(`Backend process exited with code ${code}, signal ${signal}`)
      backendProcess = null
    })
    
    backendProcess.on('error', (error) => {
      console.error('Failed to start backend process:', error)
      backendProcess = null
    })
    
    // Wait for backend to become healthy
    const isHealthy = await waitForBackend()
    
    if (!isHealthy) {
      throw new Error('Backend failed to start within timeout')
    }
    
    console.log('Backend started and healthy')
  } catch (error) {
    console.error('Error starting backend:', error)
    throw error
  }
}

/**
 * Stop the Python backend process
 */
export async function stopBackend(): Promise<void> {
  if (!backendProcess) {
    return
  }
  
  console.log('Stopping backend process...')
  
  return new Promise((resolve) => {
    if (!backendProcess) {
      resolve()
      return
    }
    
    const timeout = setTimeout(() => {
      // Force kill if graceful shutdown takes too long
      if (backendProcess) {
        console.log('Force killing backend process')
        backendProcess.kill('SIGKILL')
      }
      resolve()
    }, 5000)
    
    backendProcess.on('exit', () => {
      clearTimeout(timeout)
      backendProcess = null
      resolve()
    })
    
    // Try graceful shutdown first
    backendProcess.kill('SIGTERM')
  })
}

/**
 * Check if the backend process is running
 */
export function isBackendRunning(): boolean {
  return backendProcess !== null && !backendProcess.killed
}

/**
 * Get the backend port
 */
export function getBackendPort(): number {
  return backendPort
}

/**
 * Set the backend port (must be called before startBackend)
 */
export function setBackendPort(port: number): void {
  backendPort = port
}
