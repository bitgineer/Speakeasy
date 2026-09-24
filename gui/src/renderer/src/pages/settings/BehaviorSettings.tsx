/**
 * Behavior Settings Page
 * 
 * Configuration for app behavior like auto-paste and text cleanup.
 */

import { useEffect, useState, useRef } from 'react'
import { X } from 'lucide-react'
import { useSettingsStore } from '../../store'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { Button } from '../../components/ui/button'

interface SwitchRowProps {
  label: string
  hint: string
  checked: boolean
  disabled?: boolean
  onChange: (checked: boolean) => void
}

function SwitchRow({
  label,
  hint,
  checked,
  disabled = false,
  onChange
}: SwitchRowProps): JSX.Element {
  return (
    <label className="switch-row">
      <span className="switch-copy">
        <span className="switch-label">{label}</span>
        <span className="switch-hint">{hint}</span>
      </span>
      <input
        type="checkbox"
        className="switch"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
    </label>
  )
}

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
    custom_filler_words: '',
    live_transcription: false,
    live_chunk_seconds: 3.0,
    live_auto_paste: false,
    debug_logging: false
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
  }, []) // Remove dependencies to prevent infinite loop
  
  // Set local settings when settings are loaded
  useEffect(() => {
    if (settings) {
      const newSettings = {
        auto_paste: settings.auto_paste,
        show_recording_indicator: settings.show_recording_indicator,
        always_show_indicator: settings.always_show_indicator ?? true,
        enable_text_cleanup: settings.enable_text_cleanup ?? false,
        custom_filler_words: settings.custom_filler_words?.join(', ') ?? '',
        live_transcription: settings.live_transcription ?? false,
        live_chunk_seconds: settings.live_chunk_seconds ?? 3.0,
        live_auto_paste: settings.live_auto_paste ?? false,
        debug_logging: settings.debug_logging ?? false
      }
      
      // Only update if we haven't modified local settings yet (initial load)
      // or if we just saved
      if (saveStatus === 'idle' || saveStatus === 'saved') {
        setLocalSettings(newSettings)
        originalSettings.current = newSettings
      }
    }
  }, [settings, saveStatus])

  const handleSave = async (): Promise<void> => {
    setSaveStatus('saving')
    const success = await updateSettings({
      auto_paste: localSettings.auto_paste,
      show_recording_indicator: localSettings.show_recording_indicator,
      always_show_indicator: localSettings.always_show_indicator,
      enable_text_cleanup: localSettings.enable_text_cleanup,
      custom_filler_words: localSettings.custom_filler_words
        ? localSettings.custom_filler_words.split(',').map(s => s.trim()).filter(Boolean)
        : null,
      live_transcription: localSettings.live_transcription,
      live_chunk_seconds: localSettings.live_chunk_seconds,
      live_auto_paste: localSettings.live_auto_paste,
      debug_logging: localSettings.debug_logging
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
      <div className="workspace settings-loading">
        <span className="spinner animate-spin" role="status" aria-label="Loading behavior settings" />
      </div>
    )
  }

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / behavior</p>
          <h1>Behavior</h1>
          <p className="page-subtitle">Configure app behavior and text processing.</p>
        </div>
        <div className="page-actions">
          <SaveStatusIndicator status={saveStatus} />
          <Button
            onClick={handleSave}
            disabled={isSaving || saveStatus === 'idle' || saveStatus === 'saved'}
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
        {/* Recording Behavior */}
        <section className="card settings-panel" aria-labelledby="recording-behavior-title">
          <div className="settings-head">
            <h2 id="recording-behavior-title">Recording behavior</h2>
          </div>
          
          <div className="settings-rows">
            <SwitchRow
              label="Auto-paste after transcription"
              hint="Automatically paste transcribed text to the active window"
              checked={localSettings.auto_paste}
              disabled={isSaving}
              onChange={(checked) => setLocalSettings(prev => ({ ...prev, auto_paste: checked }))}
            />
            
            <SwitchRow
              label="Show recording indicator"
              hint="Display a visual indicator in the center of the screen while recording"
              checked={localSettings.show_recording_indicator}
              disabled={isSaving}
              onChange={(checked) =>
                setLocalSettings(prev => ({ ...prev, show_recording_indicator: checked }))
              }
            />

            {localSettings.show_recording_indicator && (
              <div className="switch-nested">
                <SwitchRow
                  label={'Always show "Ready" status'}
                  hint="Keep the indicator visible on screen when idle"
                  checked={localSettings.always_show_indicator}
                  disabled={isSaving}
                  onChange={(checked) =>
                    setLocalSettings(prev => ({ ...prev, always_show_indicator: checked }))
                  }
                />
              </div>
            )}
          </div>
        </section>

        {/* Text Cleanup */}
        <section className="card settings-panel" aria-labelledby="text-cleanup-title">
          <div className="settings-head">
            <h2 id="text-cleanup-title">Text cleanup</h2>
          </div>
          
          <div className="settings-rows">
            <SwitchRow
              label="Remove filler words"
              hint='Automatically remove common filler words like "um", "uh", "like", etc.'
              checked={localSettings.enable_text_cleanup}
              disabled={isSaving}
              onChange={(checked) =>
                setLocalSettings(prev => ({ ...prev, enable_text_cleanup: checked }))
              }
            />

            {localSettings.enable_text_cleanup && (
              <div className="field">
                <label className="label" htmlFor="custom-filler-words">
                  Additional filler words (comma-separated)
                </label>
                <input
                  id="custom-filler-words"
                  type="text"
                  value={localSettings.custom_filler_words}
                  onChange={(e) =>
                    setLocalSettings(prev => ({ ...prev, custom_filler_words: e.target.value }))
                  }
                  disabled={isSaving}
                  placeholder="e.g., basically, literally, actually"
                  className="input"
                />
              </div>
            )}
          </div>
        </section>

        {/* Live Transcription */}
        <section className="card settings-panel" aria-labelledby="live-transcription-title">
          <div className="settings-head">
            <h2 id="live-transcription-title">Live transcription</h2>
          </div>
          <div className="settings-rows">
            <SwitchRow
              label="Show live text"
              hint="Transcribe audio in real time while recording (updates every few seconds)"
              checked={localSettings.live_transcription}
              disabled={isSaving}
              onChange={(checked) =>
                setLocalSettings(prev => ({ ...prev, live_transcription: checked }))
              }
            />
            {localSettings.live_transcription && (
              <div className="settings-rows">
                <div className="field">
                  <label className="label" htmlFor="live-chunk-seconds">
                    Update interval: {localSettings.live_chunk_seconds}s
                  </label>
                  <input
                    id="live-chunk-seconds"
                    type="range"
                    min="1"
                    max="10"
                    step="0.5"
                    value={localSettings.live_chunk_seconds}
                    onChange={(e) =>
                      setLocalSettings(prev => ({
                        ...prev,
                        live_chunk_seconds: parseFloat(e.target.value)
                      }))
                    }
                    disabled={isSaving}
                    className="range"
                  />
                  <div className="range-scale">
                    <span>1s (faster)</span>
                    <span>10s (slower)</span>
                  </div>
                </div>
                <SwitchRow
                  label="Auto-paste live text"
                  hint="Automatically paste live transcripts into the active window"
                  checked={localSettings.live_auto_paste}
                  disabled={isSaving}
                  onChange={(checked) =>
                    setLocalSettings(prev => ({ ...prev, live_auto_paste: checked }))
                  }
                />
              </div>
            )}
          </div>
        </section>

        {/* Diagnostics */}
        <section className="card settings-panel" aria-labelledby="diagnostics-title">
          <div className="settings-head">
            <h2 id="diagnostics-title">Diagnostics</h2>
          </div>

          <SwitchRow
            label="Verbose debug logging"
            hint="Log every live transcription update and paste action. Applies after an app restart."
            checked={localSettings.debug_logging}
            disabled={isSaving}
            onChange={(checked) => setLocalSettings(prev => ({ ...prev, debug_logging: checked }))}
          />
        </section>
      </div>
    </div>
  )
}
