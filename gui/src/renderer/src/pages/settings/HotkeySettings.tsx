/**
 * Hotkey Settings Page
 * 
 * Configuration for keyboard shortcuts.
 */

import { useEffect, useState, useRef } from 'react'
import { useSettingsStore } from '../../store'
import HotkeyInput from '../../components/HotkeyInput'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'

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

  const [localSettings, setLocalSettings] = useState({
    hotkey: '',
    hotkey_mode: 'toggle' as 'toggle' | 'push-to-talk'
  })

  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const originalSettings = useRef(localSettings)

  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  useEffect(() => {
    const isDirty = JSON.stringify(localSettings) !== JSON.stringify(originalSettings.current)
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [localSettings, saveStatus])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  useEffect(() => {
    if (settings) {
      const newSettings = {
        hotkey: settings.hotkey,
        hotkey_mode: settings.hotkey_mode || 'toggle'
      }
      setLocalSettings(newSettings)
      originalSettings.current = newSettings
    }
  }, [settings])

  const handleSave = async (): Promise<void> => {
    setSaveStatus('saving')
    const success = await updateSettings({
      hotkey: localSettings.hotkey,
      hotkey_mode: localSettings.hotkey_mode
    })
    
    if (success) {
      setSaveStatus('saved')
      originalSettings.current = localSettings

      // Register the hotkey with Electron
      if (localSettings.hotkey && window.api) {
        await window.api.registerHotkey(localSettings.hotkey, localSettings.hotkey_mode)
      } else if (!localSettings.hotkey && window.api) {
        await window.api.unregisterHotkey()
      }
    } else {
      setSaveStatus('unsaved')
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
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Configure keyboard shortcuts for recording</p>
        </div>
        <div className="flex items-center gap-4">
          <SaveStatusIndicator status={saveStatus} />
          <button
            onClick={handleSave}
            disabled={isSaving || saveStatus === 'idle' || saveStatus === 'saved'}
            className="btn-primary"
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
        {/* Hotkey Configuration */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Recording Hotkey</h2>
          <HotkeyInput
            value={localSettings.hotkey}
            onChange={(hotkey) => setLocalSettings(prev => ({ ...prev, hotkey }))}
            disabled={isSaving}
          />
          <p className="mt-3 text-xs text-[var(--color-text-muted)]">
            Press any key combination to set it as your recording hotkey.
            The hotkey works globally even when the app is in the background.
          </p>
        </section>

        {/* Hotkey Mode */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Hotkey Mode</h2>
          <div className="flex gap-4">
            <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg border border-[var(--color-border)] flex-1 hover:bg-[var(--color-bg-tertiary)] transition-colors">
              <input
                type="radio"
                name="hotkey_mode"
                value="toggle"
                checked={localSettings.hotkey_mode === 'toggle'}
                onChange={() => setLocalSettings(prev => ({ ...prev, hotkey_mode: 'toggle' }))}
                disabled={isSaving}
                className="w-4 h-4 mt-1 text-[var(--color-accent)] bg-[var(--color-bg-secondary)] border-[var(--color-border)]"
              />
              <div>
                <span className="text-[var(--color-text-primary)] font-medium">Toggle</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-1">Press to start, press again to stop</p>
              </div>
            </label>
            <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg border border-[var(--color-border)] flex-1 hover:bg-[var(--color-bg-tertiary)] transition-colors">
              <input
                type="radio"
                name="hotkey_mode"
                value="push-to-talk"
                checked={localSettings.hotkey_mode === 'push-to-talk'}
                onChange={() => setLocalSettings(prev => ({ ...prev, hotkey_mode: 'push-to-talk' }))}
                disabled={isSaving}
                className="w-4 h-4 mt-1 text-[var(--color-accent)] bg-[var(--color-bg-secondary)] border-[var(--color-border)]"
              />
              <div>
                <span className="text-[var(--color-text-primary)] font-medium">Push-to-talk</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-1">Hold to record, release to stop</p>
              </div>
            </label>
          </div>
        </section>
      </div>
    </div>
  )
}
