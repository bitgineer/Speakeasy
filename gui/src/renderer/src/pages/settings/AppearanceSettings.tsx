/**
 * Appearance Settings Page
 * 
 * Configuration for theme and visual settings.
 */

import { useEffect, useState, useRef } from 'react'
import { Palette } from 'lucide-react'
import { useSettingsStore } from '../../store'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'

// Theme definitions with preview colors
const themes = [
  { 
    id: 'default', 
    name: 'Default', 
    description: 'Clean dark theme with indigo accent',
    colors: { bg: '#0a0a0a', accent: '#6366f1', text: '#fafafa' }
  },
  { 
    id: 'tokyo-night', 
    name: 'Tokyo Night', 
    description: 'Storm variant of the popular Tokyo Night theme',
    colors: { bg: '#1a1b26', accent: '#7aa2f7', text: '#c0caf5' }
  },
  { 
    id: 'catppuccin', 
    name: 'Catppuccin Mocha', 
    description: 'Soothing pastel theme with warm colors',
    colors: { bg: '#1e1e2e', accent: '#89b4fa', text: '#cdd6f4' }
  },
  { 
    id: 'gruvbox', 
    name: 'Gruvbox Dark', 
    description: 'Retro groove colors with warm tones',
    colors: { bg: '#282828', accent: '#83a598', text: '#ebdbb2' }
  },
  { 
    id: 'everforest', 
    name: 'Everforest', 
    description: 'Green forest-inspired comfortable colors',
    colors: { bg: '#2b3339', accent: '#a7c080', text: '#d3c6aa' }
  },
  { 
    id: 'nord', 
    name: 'Nord', 
    description: 'Arctic, north-bluish color palette',
    colors: { bg: '#2e3440', accent: '#88c0d0', text: '#eceff4' }
  },
  { 
    id: 'kanagawa', 
    name: 'Kanagawa Wave', 
    description: 'Inspired by the great wave off Kanagawa',
    colors: { bg: '#1f1f28', accent: '#7e9cd8', text: '#dcd7ba' }
  },
  { 
    id: 'ayu', 
    name: 'Ayu Dark', 
    description: 'Simple, bright colors with warm accent',
    colors: { bg: '#0b0e14', accent: '#e6b450', text: '#bfbdb6' }
  },
  { 
    id: 'one-dark', 
    name: 'One Dark', 
    description: 'Atom One Dark theme colors',
    colors: { bg: '#282c34', accent: '#61afef', text: '#abb2bf' }
  }
]

export default function AppearanceSettings(): JSX.Element {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    fetchSettings,
    updateSettings,
    clearError
  } = useSettingsStore()

  // Initialize from settings if available, otherwise null (not 'default')
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const originalTheme = useRef<string | null>(null)

  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  useEffect(() => {
    // Don't track dirty state until settings are loaded
    if (selectedTheme === null) return
    
    const isDirty = selectedTheme !== originalTheme.current
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [selectedTheme, saveStatus])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  useEffect(() => {
    if (settings?.theme) {
      setSelectedTheme(settings.theme)
      originalTheme.current = settings.theme
    }
  }, [settings])

  // Apply theme immediately for preview - but only after initial load
  useEffect(() => {
    if (selectedTheme) {
      document.documentElement.setAttribute('data-theme', selectedTheme)
    }
  }, [selectedTheme])

  const handleSave = async (): Promise<void> => {
    if (!selectedTheme) return
    
    setSaveStatus('saving')
    const success = await updateSettings({
      theme: selectedTheme
    })
    
    if (success) {
      setSaveStatus('saved')
      originalTheme.current = selectedTheme
    } else {
      setSaveStatus('unsaved')
    }
  }

  const handleThemeChange = (themeId: string) => {
    setSelectedTheme(themeId)
    // Apply immediately for preview
    document.documentElement.setAttribute('data-theme', themeId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl min-h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Palette className="w-6 h-6 text-[var(--color-accent-primary)]" />
          <h1 className="text-2xl font-bold">Appearance</h1>
        </div>
        <SaveStatusIndicator status={saveStatus} onSave={saveSettings} />
      </div>

      <div className="space-y-6 flex-1 flex flex-col">
        <section className="card p-4 flex-1">
          <h2 className="text-lg font-semibold mb-4">Theme</h2>
          <div className="grid grid-cols-1 gap-3">
            {themes.map((theme) => (
              <label
                key={theme.id}
                className={`
                  flex items-center gap-4 p-3 rounded-lg border cursor-pointer
                  transition-all duration-150 ease-out
                  ${selectedTheme === theme.id 
                    ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)]' 
                    : 'border-[var(--color-border)] hover:bg-[var(--color-bg-tertiary)]'
                  }
                `}
              >
                <input
                  type="radio"
                  name="theme"
                  value={theme.id}
                  checked={selectedTheme === theme.id}
                  onChange={() => handleThemeChange(theme.id)}
                  disabled={isSaving || selectedTheme === null}
                  className="sr-only"
                />
                
                {/* Color preview */}
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0 border border-white/10"
                  style={{ backgroundColor: theme.colors.bg }}
                >
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: theme.colors.accent }}
                  />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-[var(--color-text-primary)]">{theme.name}</span>
                    {selectedTheme === theme.id && (
                      <svg className="w-4 h-4 text-[var(--color-accent)]" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">{theme.description}</p>
                </div>
              </label>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
