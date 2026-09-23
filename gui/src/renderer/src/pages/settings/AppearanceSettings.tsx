/**
 * Appearance Settings Page
 *
 * Theme (Light, Dark, System) and accent (Violet, Ink) selection.
 */

import { useEffect, useRef, useState } from 'react'
import { Check, Monitor, Moon, Palette, Sun } from 'lucide-react'
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
import { cn } from '@/lib/utils'

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
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-edge-control border-t-accent-solid rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Palette className="w-6 h-6 text-accent-text" />
          <h1 className="text-page font-semibold">Appearance</h1>
        </div>
        <SaveStatusIndicator status={saveStatus} onSave={handleSave} />
      </div>

      <div className="space-y-6">
        <section className="card p-4">
          <h2 className="text-heading font-semibold mb-4">Theme</h2>
          <div className="grid grid-cols-1 gap-3">
            {themeOptions.map((option) => {
              const ThemeIcon = option.icon
              const selected = selectedTheme === option.id
              return (
                <label
                  key={option.id}
                  className={cn(
                    'flex items-center gap-4 p-3 rounded-panel border cursor-pointer',
                    'transition-[border-color,background-color] duration-fast ease-standard',
                    selected
                      ? 'border-accent-solid bg-accent-muted'
                      : 'border-edge-subtle bg-surface-raised hover:border-edge-strong'
                  )}
                >
                  <input
                    type="radio"
                    name="theme"
                    value={option.id}
                    checked={selected}
                    onChange={() => setSelectedTheme(option.id)}
                    disabled={isSaving || selectedTheme === null}
                    className="sr-only"
                  />

                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-surface-sunken text-content-secondary">
                    <ThemeIcon className="h-5 w-5" aria-hidden="true" />
                  </span>

                  <span className="flex-1 min-w-0">
                    <span className="flex items-center gap-2 text-ui font-medium text-content-primary">
                      {option.name}
                      {selected && (
                        <Check className="h-4 w-4 text-accent-text" aria-hidden="true" />
                      )}
                    </span>
                    <span className="block text-small text-content-muted mt-0.5 truncate">
                      {option.description}
                    </span>
                  </span>
                </label>
              )
            })}
          </div>
        </section>

        <section className="card p-4">
          <h2 className="text-heading font-semibold mb-4">Accent</h2>
          <div className="grid grid-cols-1 gap-3">
            {accentOptions.map((option) => {
              const selected = selectedAccent === option.id
              return (
                <label
                  key={option.id}
                  className={cn(
                    'flex items-center gap-4 p-3 rounded-panel border cursor-pointer',
                    'transition-[border-color,background-color] duration-fast ease-standard',
                    selected
                      ? 'border-accent-solid bg-accent-muted'
                      : 'border-edge-subtle bg-surface-raised hover:border-edge-strong'
                  )}
                >
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
                    className="h-10 w-10 shrink-0 rounded-control border border-edge-subtle"
                    style={{ backgroundColor: option.preview }}
                    aria-hidden="true"
                  />

                  <span className="flex-1 min-w-0">
                    <span className="flex items-center gap-2 text-ui font-medium text-content-primary">
                      {option.name}
                      {selected && (
                        <Check className="h-4 w-4 text-accent-text" aria-hidden="true" />
                      )}
                    </span>
                    <span className="block text-small text-content-muted mt-0.5 truncate">
                      {option.description}
                    </span>
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
