/**
 * Hotkey Settings Page
 *
 * Edits the global hotkey binding list: accelerator, trigger, and mode.
 */

import { useEffect, useState, useRef } from 'react'
import { Trash2, X } from 'lucide-react'
import { useSettingsStore } from '../../store'
import { useToast } from '../../hooks/useToast'
import HotkeyInput from '../../components/HotkeyInput'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { Button } from '../../components/ui/button'
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
      <div className="workspace settings-loading">
        <span className="spinner animate-spin" role="status" aria-label="Loading hotkey settings" />
      </div>
    )
  }

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / hotkey</p>
          <h1>Hotkey Settings</h1>
          <p className="page-subtitle">
            Global shortcuts for recording. Each binding can dedicate a processing mode.
          </p>
        </div>
        <div className="page-actions">
          <SaveStatusIndicator status={saveStatus} />
          <Button
            onClick={handleSave}
            disabled={isSaving || invalid || saveStatus === 'idle' || saveStatus === 'saved'}
            title={invalid ? 'Every binding needs a unique, non-empty accelerator' : undefined}
          >
            {isSaving ? 'Saving...' : 'Save changes'}
          </Button>
        </div>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button
            type="button"
            onClick={clearError}
            title="Dismiss error"
            aria-label="Dismiss error"
          >
            <X size={14} aria-hidden="true" />
          </button>
        </div>
      )}

      <div className="settings-stack">
        <section className="card settings-panel" aria-labelledby="recording-hotkeys-title">
          <div className="settings-head">
            <h2 id="recording-hotkeys-title">Recording hotkeys</h2>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                setBindings((current) => [
                  ...current,
                  { accelerator: '', trigger: 'toggle', mode: null }
                ])
              }
              disabled={isSaving}
            >
              Add binding
            </Button>
          </div>

          {bindings.length === 0 ? (
            <p className="empty-panel">
              No hotkeys configured. Recording still works from the overlay.
            </p>
          ) : (
            <div className="settings-rows">
              {bindings.map((binding, index) => (
                <div key={index} className="subpanel">
                  <div className="input-row">
                    <HotkeyInput
                      value={binding.accelerator}
                      onChange={(accelerator) => updateBinding(index, { accelerator })}
                      disabled={isSaving}
                      label=""
                      hint=""
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setBindings((current) => current.filter((_, i) => i !== index))
                      }
                      disabled={isSaving}
                      className="icon-button"
                      data-tone="danger"
                      title="Remove binding"
                      aria-label="Remove binding"
                    >
                      <Trash2 size={15} aria-hidden="true" />
                    </button>
                  </div>
                  <div className="field-grid">
                    <div className="field">
                      <label className="label" htmlFor={`hotkey-trigger-${index}`}>
                        Trigger
                      </label>
                      <select
                        id={`hotkey-trigger-${index}`}
                        value={binding.trigger}
                        onChange={(e) =>
                          updateBinding(index, {
                            trigger: e.target.value as HotkeyBinding['trigger']
                          })
                        }
                        disabled={isSaving}
                        className="select"
                      >
                        {TRIGGERS.map((trigger) => (
                          <option key={trigger} value={trigger}>
                            {trigger === 'toggle' ? 'Toggle' : 'Push-to-talk'}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="field">
                      <label className="label" htmlFor={`hotkey-mode-${index}`}>
                        Mode
                      </label>
                      <select
                        id={`hotkey-mode-${index}`}
                        value={binding.mode ?? ''}
                        onChange={(e) =>
                          updateBinding(index, {
                            mode: e.target.value === '' ? null : (e.target.value as ProcessingMode)
                          })
                        }
                        disabled={isSaving}
                        className="select"
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
                    <p className="field-error">This accelerator is used by another binding.</p>
                  )}
                </div>
              ))}
            </div>
          )}

          <p className="settings-note">
            Toggle starts and stops on each press. Push-to-talk records while held; hold for 60
            seconds to lock the recording. Bindings set to &quot;Active mode&quot; use the mode
            selected on the Dashboard.
          </p>
        </section>
      </div>
    </div>
  )
}
