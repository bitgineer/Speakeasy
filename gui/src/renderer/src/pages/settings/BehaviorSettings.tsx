/**
 * Behavior Settings Page
 * 
 * Configuration for app behavior like auto-paste and text cleanup.
 */

import { useEffect, useState, useRef } from 'react'
import { useSettingsStore } from '../../store'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'

export default function BehaviorSettings(): JSX.Element {
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
    auto_paste: true,
    show_recording_indicator: true,
    always_show_indicator: true,
    enable_text_cleanup: false,
    custom_filler_words: ''
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
        auto_paste: settings.auto_paste,
        show_recording_indicator: settings.show_recording_indicator,
        always_show_indicator: settings.always_show_indicator ?? true,
        enable_text_cleanup: settings.enable_text_cleanup ?? false,
        custom_filler_words: settings.custom_filler_words?.join(', ') ?? ''
      }
      setLocalSettings(newSettings)
      originalSettings.current = newSettings
    }
  }, [settings])

  const handleSave = async (): Promise<void> => {
    setSaveStatus('saving')
    const success = await updateSettings({
      auto_paste: localSettings.auto_paste,
      show_recording_indicator: localSettings.show_recording_indicator,
      always_show_indicator: localSettings.always_show_indicator,
      enable_text_cleanup: localSettings.enable_text_cleanup,
      custom_filler_words: localSettings.custom_filler_words
        ? localSettings.custom_filler_words.split(',').map(s => s.trim()).filter(Boolean)
        : null
    })
    
    if (success) {
      setSaveStatus('saved')
      originalSettings.current = localSettings
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
          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Behavior</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Configure app behavior and text processing</p>
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
        {/* Recording Behavior */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Recording Behavior</h2>
          
          <div className="space-y-4">
            {/* Auto-paste toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-[var(--color-text-primary)]">Auto-paste after transcription</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Automatically paste transcribed text to the active window
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={localSettings.auto_paste}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, auto_paste: e.target.checked }))}
                  disabled={isSaving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
              </div>
            </label>
            
            {/* Recording indicator toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-[var(--color-text-primary)]">Show recording indicator</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Display a visual indicator in the center of the screen while recording
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={localSettings.show_recording_indicator}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, show_recording_indicator: e.target.checked }))}
                  disabled={isSaving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
              </div>
            </label>

            {/* Always show indicator toggle */}
            {localSettings.show_recording_indicator && (
              <label className="flex items-center justify-between cursor-pointer ml-6 pl-4 border-l-2 border-[var(--color-border)] animate-in fade-in slide-in-from-top-2 duration-200">
                <div>
                  <span className="text-[var(--color-text-primary)]">Always show "Ready" status</span>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    Keep the indicator visible on screen when idle
                  </p>
                </div>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={localSettings.always_show_indicator}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, always_show_indicator: e.target.checked }))}
                    disabled={isSaving}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
                </div>
              </label>
            )}
          </div>
        </section>

        {/* Text Cleanup */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Text Cleanup</h2>
          
          <div className="space-y-4">
            {/* Text cleanup toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-[var(--color-text-primary)]">Remove filler words</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Automatically remove common filler words like "um", "uh", "like", etc.
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={localSettings.enable_text_cleanup}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, enable_text_cleanup: e.target.checked }))}
                  disabled={isSaving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
              </div>
            </label>

            {/* Custom filler words input */}
            {localSettings.enable_text_cleanup && (
              <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                <label className="label">Additional filler words (comma-separated)</label>
                <input
                  type="text"
                  value={localSettings.custom_filler_words}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, custom_filler_words: e.target.value }))}
                  disabled={isSaving}
                  placeholder="e.g., basically, literally, actually"
                  className="input w-full"
                />
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
