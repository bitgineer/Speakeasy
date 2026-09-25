import { useEffect, useState } from 'react'
import { useSettingsStore } from '../store'
import { apiClient } from '../api/client'
import type { ModeStatusResponse, ProcessingMode } from '../api/types'

const CHIPS: { mode: ProcessingMode; label: string }[] = [
  { mode: 'write', label: 'Write' },
  { mode: 'command', label: 'Command' },
  { mode: 'dictate', label: 'Dictate' }
]

export default function ModeChips(): JSX.Element {
  const { settings, isSaving, updateSettings } = useSettingsStore()
  const [statuses, setStatuses] = useState<ModeStatusResponse[]>([])

  useEffect(() => {
    let cancelled = false

    apiClient
      .getProcessingStatus()
      .then((status) => {
        if (!cancelled) setStatuses(status.modes)
      })
      .catch(() => {
        if (!cancelled) setStatuses([])
      })

    return () => {
      cancelled = true
    }
  }, [settings?.active_mode, settings?.active_provider_id, settings?.providers])

  const activeMode = settings?.active_mode

  return (
    <div className="segmented" role="group" aria-label="Processing mode">
      {CHIPS.map(({ mode, label }) => {
        const status = statuses.find((entry) => entry.mode === mode)
        const notReady = mode !== 'dictate' && status !== undefined && !status.ready
        const active = activeMode === mode

        return (
          <button
            key={mode}
            type="button"
            aria-pressed={active}
            onClick={() => void updateSettings({ active_mode: mode })}
            disabled={isSaving}
            title={notReady ? status.reason ?? `${label} is not ready` : `Use ${label} mode`}
          >
            {label}
            {notReady && <span className="chip-warning" aria-hidden="true" />}
          </button>
        )
      })}
    </div>
  )
}
