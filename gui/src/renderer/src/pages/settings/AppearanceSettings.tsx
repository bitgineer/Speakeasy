/**
 * Appearance Settings Page
 *
 * Theme (Light, Dark, System) and accent (Violet, Ink) selection.
 */

import { useEffect, useRef, useState } from 'react'
import { Check, Monitor, Moon, Sun } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useSettingsStore } from '../../store'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import {
  type AccentSetting,
  type ThemeSetting,
  applyAppearance,
  readStoredAccent,
  resolveTheme,
  resolveThemeSetting,
  storeAccent,
  useSystemPrefersDark
} from '../../utils/theme'

const themeOptions: {
  id: ThemeSetting
  name: string
  description: string
  icon: LucideIcon
}[] = [
  { id: 'light', name: 'Light', description: 'Warm paper surfaces for daylight', icon: Sun },
  { id: 'dark', name: 'Dark', description: 'Near-black surfaces with a violet accent', icon: Moon },
  { id: 'system', name: 'System', description: 'Follow the system light or dark setting', icon: Monitor }
]

const accentOptions: {
  id: AccentSetting
  name: string
  description: string
  preview: string
}[] = [
  { id: 'violet', name: 'Violet', description: 'The app\u2019s original accent', preview: 'var(--accent-preview-violet)' },
  { id: 'ink', name: 'Ink', description: 'Quiet blue for light-first use', preview: 'var(--accent-preview-ink)' }
]

export default function AppearanceSettings(): JSX.Element {
  const {
    settings,
    isLoading,
    isSaving,
    fetchSettings,
    updateSettings
  } = useSettingsStore()

  const [selectedTheme, setSelectedTheme] = useState<ThemeSetting | null>(null)
  const [selectedAccent, setSelectedAccent] = useState<AccentSetting>(() => readStoredAccent())
  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const originalTheme = useRef<ThemeSetting | null>(null)
  const originalAccent = useRef<AccentSetting>(selectedAccent)
  const systemPrefersDark = useSystemPrefersDark()

  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  useEffect(() => {
    if (selectedTheme === null) return

    const isDirty =
      selectedTheme !== originalTheme.current || selectedAccent !== originalAccent.current
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [selectedTheme, selectedAccent, saveStatus])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  useEffect(() => {
    if (!settings?.theme) return

    const resolved = resolveThemeSetting(settings.theme)
    setSelectedTheme(resolved)
    originalTheme.current = resolved
  }, [settings])

  // Apply both choices immediately for preview
  useEffect(() => {
    if (selectedTheme === null) return

    applyAppearance(resolveTheme(selectedTheme, systemPrefersDark), selectedAccent)
  }, [selectedTheme, selectedAccent, systemPrefersDark])

  const handleSave = async (): Promise<void> => {
    if (!selectedTheme) return

    setSaveStatus('saving')
    const success = await updateSettings({
      theme: selectedTheme
    })

    if (success) {
      storeAccent(selectedAccent)
      originalTheme.current = selectedTheme
      originalAccent.current = selectedAccent
      setSaveStatus('saved')
    } else {
      setSaveStatus('unsaved')
    }
  }

  if (isLoading) {
    return (
      <div className="workspace settings-loading">
        <span className="spinner animate-spin" role="status" aria-label="Loading appearance settings" />
      </div>
    )
  }

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / appearance</p>
          <h1>Appearance</h1>
          <p className="page-subtitle">Theme and accent color for the interface.</p>
        </div>
        <div className="page-actions">
          <SaveStatusIndicator status={saveStatus} onSave={handleSave} />
        </div>
      </header>

      <div className="settings-stack">
        <section className="card settings-panel" aria-labelledby="theme-title">
          <div className="settings-head">
            <h2 id="theme-title">Theme</h2>
          </div>
          <div className="option-list">
            {themeOptions.map((option) => {
              const ThemeIcon = option.icon
              const selected = selectedTheme === option.id
              return (
                <label key={option.id} className="option" data-selected={selected}>
                  <input
                    type="radio"
                    name="theme"
                    value={option.id}
                    checked={selected}
                    onChange={() => setSelectedTheme(option.id)}
                    disabled={isSaving || selectedTheme === null}
                    className="sr-only"
                  />

                  <span className="option-icon">
                    <ThemeIcon size={18} strokeWidth={1.75} aria-hidden="true" />
                  </span>

                  <span className="option-body">
                    <span className="option-title">
                      {option.name}
                      {selected && (
                        <Check className="text-accent-text" size={14} aria-hidden="true" />
                      )}
                    </span>
                    <span className="option-meta">{option.description}</span>
                  </span>
                </label>
              )
            })}
          </div>
        </section>

        <section className="card settings-panel" aria-labelledby="accent-title">
          <div className="settings-head">
            <h2 id="accent-title">Accent</h2>
          </div>
          <div className="option-list">
            {accentOptions.map((option) => {
              const selected = selectedAccent === option.id
              return (
                <label key={option.id} className="option" data-selected={selected}>
                  <input
                    type="radio"
                    name="accent"
                    value={option.id}
                    checked={selected}
                    onChange={() => setSelectedAccent(option.id)}
                    disabled={isSaving}
                    className="sr-only"
                  />

                  <span
                    className="option-swatch"
                    style={{ backgroundColor: option.preview }}
                    aria-hidden="true"
                  />

                  <span className="option-body">
                    <span className="option-title">
                      {option.name}
                      {selected && (
                        <Check className="text-accent-text" size={14} aria-hidden="true" />
                      )}
                    </span>
                    <span className="option-meta">{option.description}</span>
                  </span>
                </label>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}
