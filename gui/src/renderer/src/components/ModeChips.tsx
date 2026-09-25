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
    <div className="flex items-center gap-0.5 p-0.5 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg">
      {CHIPS.map(({ mode, label }) => {
        const status = statuses.find((entry) => entry.mode === mode)
        const notReady = mode !== 'dictate' && status !== undefined && !status.ready
        const active = activeMode === mode

        return (
          <button
            key={mode}
            type="button"
            onClick={() => void updateSettings({ active_mode: mode })}
            disabled={isSaving}
            title={notReady ? status.reason ?? `${label} is not ready` : `Use ${label} mode`}
            className={`
              flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150 cursor-pointer
              ${active
                ? 'bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)] shadow-sm'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'}
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {label}
            {notReady && (
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-warning)]" aria-hidden />
            )}
          </button>
        )
      })}
    </div>
  )
}
