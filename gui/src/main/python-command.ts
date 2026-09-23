/** Chooses how to launch the Python backend, with no Electron imports. */

export type BackendCommand =
  | { ok: true; cmd: string; args: string[] }
  | { ok: false; reason: 'missing-backend-environment' }

export interface BackendCommandOptions {
  isPackaged: boolean
  port: number
  uvAvailable: boolean
  uvLockExists: boolean
  backendVenvPython: string | null
  rootVenvPython: string | null
  systemPython: string
}

export function chooseBackendCommand(options: BackendCommandOptions): BackendCommand {
  const {
    isPackaged,
    port,
    uvAvailable,
    uvLockExists,
    backendVenvPython,
    rootVenvPython,
    systemPython
  } = options
  const args = ['-m', 'speakeasy', '--port', String(port)]

  if (!isPackaged && uvAvailable && uvLockExists) {
    return { ok: true, cmd: 'uv', args: ['run', ...args] }
  }

  if (backendVenvPython) {
    return { ok: true, cmd: backendVenvPython, args }
  }

  if (rootVenvPython) {
    return { ok: true, cmd: rootVenvPython, args }
  }

  if (!isPackaged) {
    return { ok: true, cmd: systemPython, args }
  }

  return { ok: false, reason: 'missing-backend-environment' }
}
