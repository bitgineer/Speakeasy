import { useEffect, useRef } from 'react'
import type { HotkeyBinding, HotkeyRegistrationFailure } from '../api/types'

/**
 * Pushes the current bindings to the Electron main process whenever they change
 * and reports any accelerators that could not be registered.
 */
export function useHotkeyRegistration(
  bindings: HotkeyBinding[] | undefined,
  onFailure: (failed: HotkeyRegistrationFailure[]) => void
): void {
  const failureHandler = useRef(onFailure)

  useEffect(() => {
    failureHandler.current = onFailure
  })

  useEffect(() => {
    if (!window.api || !bindings) return

    window.api.registerHotkeys(bindings).then((result) => {
      if (!result.ok) failureHandler.current(result.failed)
    })
  }, [bindings])
}
