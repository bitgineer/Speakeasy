/**
 * Hotkey Settings Page
 *
 * Edits the global hotkey binding list: accelerator, trigger, and mode.
 */

import { useEffect, useState, useRef } from 'react'
import { useSettingsStore } from '../../store'
import { useToast } from '../../hooks/useToast'
import HotkeyInput from '../../components/HotkeyInput'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import type { HotkeyBinding, ProcessingMode, Settings } from '../../api/types'

const TRIGGERS: HotkeyBinding['trigger'][] = ['toggle', 'push-to-talk']
const MODES: { value: '' | ProcessingMode; label: string }[] = [
  { value: '', label: 'Active mode' },
  { value: 'write', label: 'Write' },
  { value: 'command', label: 'Command' },
  { value: 'dictate', label: 'Dictate' }
]

function toDraft(settings: Settings): HotkeyBinding[] {
  return (settings.hotkeys ?? []).map((binding) => ({
    accelerator: binding.accelerator,
    trigger: binding.trigger,
    mode: binding.mode ?? null
  }))
}

export default function HotkeySettings(): JSX.Element {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    fetchSettings,
    updateSettings,
    clearError
  } = useSettingsStore()
  const { toast } = useToast()

  const [bindings, setBindings] = useState<HotkeyBinding[]>([])
  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const originalSettings = useRef<HotkeyBinding[]>([])

  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  useEffect(() => {
    if (settings) {
      const draft = toDraft(settings)
      setBindings(draft)
      originalSettings.current = draft
    }
  }, [settings])

  useEffect(() => {
    const isDirty = JSON.stringify(bindings) !== JSON.stringify(originalSettings.current)
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [bindings, saveStatus])

  const updateBinding = (index: number, patch: Partial<HotkeyBinding>): void => {
    setBindings((current) =>
      current.map((binding, i) => (i === index ? { ...binding, ...patch } : binding))
    )
  }

  const duplicateAccelerator = (index: number): boolean => {
    const accelerator = bindings[index]?.accelerator.trim().toLowerCase()
    if (!accelerator) return false
    return bindings.some(
      (binding, i) => i !== index && binding.accelerator.trim().toLowerCase() === accelerator
    )
  }

  const invalid =
    bindings.some((binding) => binding.accelerator.trim() === '') ||
    bindings.some((_, index) => duplicateAccelerator(index))

  const handleSave = async (): Promise<void> => {
    if (invalid) return
    setSaveStatus('saving')
    const payload = bindings.map((binding) => ({ ...binding, accelerator: binding.accelerator.trim() }))
    const success = await updateSettings({ hotkeys: payload })

    if (!success) {
      setSaveStatus('unsaved')
      return
    }

    setSaveStatus('saved')
    originalSettings.current = payload

    if (window.api) {
      const result = await window.api.registerHotkeys(payload)
      if (!result.ok) {
        const failed = result.failed.map((failure) => failure.accelerator).join(', ')
        toast.error(
          `Hotkeys were saved but could not be registered: ${failed}. Another app may be using them.`
        )
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Hotkey Settings</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Global shortcuts for recording. Each binding can dedicate a processing mode.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <SaveStatusIndicator status={saveStatus} />
          <button
            onClick={handleSave}
            disabled={isSaving || invalid || saveStatus === 'idle' || saveStatus === 'saved'}
            className="btn-primary"
            title={invalid ? 'Every binding needs a unique, non-empty accelerator' : undefined}
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-3 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg flex items-center justify-between">
          <span className="text-[var(--color-error)] text-sm">{error}</span>
          <button onClick={clearError} className="text-[var(--color-error)] hover:opacity-80">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="space-y-6">
        <section className="card p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-medium text-[var(--color-text-primary)]">Recording Hotkeys</h2>
            <button
              onClick={() =>
                setBindings((current) => [
                  ...current,
                  { accelerator: '', trigger: 'toggle', mode: null }
                ])
              }
              disabled={isSaving}
              className="px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg border border-[var(--color-border)] transition-colors disabled:opacity-50"
            >
              Add binding
            </button>
          </div>

          {bindings.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
              No hotkeys configured. Recording still works from the overlay.
            </p>
          ) : (
            <div className="space-y-4">
              {bindings.map((binding, index) => (
                <div
                  key={index}
                  className="p-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-tertiary)] space-y-3"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-1">
                      <HotkeyInput
                        value={binding.accelerator}
                        onChange={(accelerator) => updateBinding(index, { accelerator })}
                        disabled={isSaving}
                        label=""
                        hint=""
                      />
                    </div>
                    <button
                      onClick={() =>
                        setBindings((current) => current.filter((_, i) => i !== index))
                      }
                      disabled={isSaving}
                      className="mt-1 p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-error)] rounded transition-colors disabled:opacity-50"
                      title="Remove binding"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <label className="label">Trigger</label>
                      <select
                        value={binding.trigger}
                        onChange={(e) =>
                          updateBinding(index, {
                            trigger: e.target.value as HotkeyBinding['trigger']
                          })
                        }
                        disabled={isSaving}
                        className="select w-full"
                      >
                        {TRIGGERS.map((trigger) => (
                          <option key={trigger} value={trigger}>
                            {trigger === 'toggle' ? 'Toggle' : 'Push-to-talk'}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="flex-1">
                      <label className="label">Mode</label>
                      <select
                        value={binding.mode ?? ''}
                        onChange={(e) =>
                          updateBinding(index, {
                            mode: e.target.value === '' ? null : (e.target.value as ProcessingMode)
                          })
                        }
                        disabled={isSaving}
                        className="select w-full"
                      >
                        {MODES.map((mode) => (
                          <option key={mode.value} value={mode.value}>
                            {mode.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  {duplicateAccelerator(index) && (
                    <p className="text-xs text-[var(--color-error)]">
                      This accelerator is used by another binding.
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          <p className="mt-4 text-xs text-[var(--color-text-muted)]">
            Toggle starts and stops on each press. Push-to-talk records while held; hold for 60
            seconds to lock the recording. Bindings set to &quot;Active mode&quot; use the mode
            selected on the Dashboard.
          </p>
        </section>
      </div>
    </div>
  )
}
