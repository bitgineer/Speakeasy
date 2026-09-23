import { describe, expect, it } from 'vitest'
import { chooseBackendCommand, type BackendCommandOptions } from './python-command'

const BACKEND_VENV = '/repo/backend/.venv/bin/python'
const ROOT_VENV = '/repo/.venv/bin/python'

function options(overrides: Partial<BackendCommandOptions> = {}): BackendCommandOptions {
  return {
    isPackaged: false,
    port: 8765,
    uvAvailable: false,
    uvLockExists: false,
    backendVenvPython: null,
    rootVenvPython: null,
    systemPython: 'python3',
    ...overrides
  }
}

describe('chooseBackendCommand', () => {
  it('uses the backend venv in a packaged build', () => {
    const command = chooseBackendCommand(
      options({
        isPackaged: true,
        uvAvailable: true,
        uvLockExists: true,
        backendVenvPython: BACKEND_VENV,
        rootVenvPython: ROOT_VENV
      })
    )

    expect(command).toEqual({
      ok: true,
      cmd: BACKEND_VENV,
      args: ['-m', 'speakeasy', '--port', '8765']
    })
  })

  it('uses the root venv in a packaged build when the backend venv is missing', () => {
    const command = chooseBackendCommand(
      options({ isPackaged: true, rootVenvPython: ROOT_VENV })
    )

    expect(command).toEqual({
      ok: true,
      cmd: ROOT_VENV,
      args: ['-m', 'speakeasy', '--port', '8765']
    })
  })

  it('returns missing-backend-environment for a packaged build with no venv, even with uv and uv.lock', () => {
    const command = chooseBackendCommand(
      options({ isPackaged: true, uvAvailable: true, uvLockExists: true })
    )

    expect(command).toEqual({ ok: false, reason: 'missing-backend-environment' })
  })

  it('uses uv in a dev build when uv and uv.lock are available', () => {
    const command = chooseBackendCommand(
      options({ port: 9999, uvAvailable: true, uvLockExists: true })
    )

    expect(command).toEqual({
      ok: true,
      cmd: 'uv',
      args: ['run', '-m', 'speakeasy', '--port', '9999']
    })
  })

  it('uses the backend venv in a dev build when uv is available but uv.lock is missing', () => {
    const command = chooseBackendCommand(
      options({ uvAvailable: true, uvLockExists: false, backendVenvPython: BACKEND_VENV })
    )

    expect(command).toEqual({
      ok: true,
      cmd: BACKEND_VENV,
      args: ['-m', 'speakeasy', '--port', '8765']
    })
  })

  it('uses the root venv in a dev build when the backend venv is missing', () => {
    const command = chooseBackendCommand(options({ rootVenvPython: ROOT_VENV }))

    expect(command).toEqual({
      ok: true,
      cmd: ROOT_VENV,
      args: ['-m', 'speakeasy', '--port', '8765']
    })
  })

  it('falls back to system python in a dev build when nothing else is available', () => {
    const command = chooseBackendCommand(options({ systemPython: 'python3' }))

    expect(command).toEqual({
      ok: true,
      cmd: 'python3',
      args: ['-m', 'speakeasy', '--port', '8765']
    })
  })
})
