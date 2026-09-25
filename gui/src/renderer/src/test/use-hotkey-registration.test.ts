import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useHotkeyRegistration } from '../hooks/useHotkeyRegistration'
import type { HotkeyBinding } from '../api/types'

const BINDING: HotkeyBinding = { accelerator: 'ctrl+shift+w', trigger: 'toggle', mode: null }

function mockRegisterHotkeys(registerHotkeys: ReturnType<typeof vi.fn>): void {
  Object.defineProperty(window, 'api', {
    value: { registerHotkeys },
    configurable: true
  })
}

describe('useHotkeyRegistration', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'api', { value: undefined, configurable: true })
  })

  it('registers the bindings and reports nothing on success', async () => {
    const registerHotkeys = vi.fn().mockResolvedValue({ ok: true })
    mockRegisterHotkeys(registerHotkeys)

    const onFailure = vi.fn()
    renderHook(() => useHotkeyRegistration([BINDING], onFailure))

    await waitFor(() => expect(registerHotkeys).toHaveBeenCalledWith([BINDING]))
    expect(onFailure).not.toHaveBeenCalled()
  })

  it('reports failed accelerators when registration is not ok', async () => {
    const failed = [{ accelerator: 'ctrl+shift+w', error: 'failed to register' }]
    const registerHotkeys = vi.fn().mockResolvedValue({ ok: false, failed })
    mockRegisterHotkeys(registerHotkeys)

    const onFailure = vi.fn()
    renderHook(() => useHotkeyRegistration([BINDING], onFailure))

    await waitFor(() => expect(onFailure).toHaveBeenCalledWith(failed))
  })

  it('does nothing when there are no bindings or no API', () => {
    const registerHotkeys = vi.fn()
    mockRegisterHotkeys(registerHotkeys)

    renderHook(() => useHotkeyRegistration(undefined, vi.fn()))

    expect(registerHotkeys).not.toHaveBeenCalled()
  })
})
