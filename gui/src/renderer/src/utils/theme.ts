import { useEffect, useState } from 'react'

export const THEME_SETTINGS = ['light', 'dark', 'system'] as const
export type ThemeSetting = (typeof THEME_SETTINGS)[number]

export const ACCENTS = ['violet', 'ink'] as const
export type AccentSetting = (typeof ACCENTS)[number]

export type ResolvedTheme = 'light' | 'dark'

export const ACCENT_STORAGE_KEY = 'speakeasy.accent'

export function resolveThemeSetting(stored: string | null | undefined): ThemeSetting {
  if (stored === 'light' || stored === 'dark' || stored === 'system') return stored
  return 'dark'
}

export function resolveTheme(setting: ThemeSetting, systemPrefersDark: boolean): ResolvedTheme {
  if (setting === 'system') return systemPrefersDark ? 'dark' : 'light'
  return setting
}

export function applyAppearance(theme: ResolvedTheme, accent: AccentSetting): void {
  const root = document.documentElement
  root.dataset.theme = theme
  root.dataset.accent = accent
}

export function readStoredAccent(): AccentSetting {
  try {
    return window.localStorage.getItem(ACCENT_STORAGE_KEY) === 'ink' ? 'ink' : 'violet'
  } catch {
    return 'violet'
  }
}

export function storeAccent(accent: AccentSetting): void {
  try {
    window.localStorage.setItem(ACCENT_STORAGE_KEY, accent)
  } catch {
    // Sandboxed windows and jsdom can refuse storage; the choice still applies for this session.
  }
}

function systemDarkQuery(): MediaQueryList | null {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return null
  return window.matchMedia('(prefers-color-scheme: dark)')
}

export function useSystemPrefersDark(): boolean {
  const [prefersDark, setPrefersDark] = useState(() => systemDarkQuery()?.matches ?? false)

  useEffect(() => {
    const query = systemDarkQuery()
    if (!query) return

    const onChange = (event: MediaQueryListEvent): void => setPrefersDark(event.matches)
    setPrefersDark(query.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])

  return prefersDark
}
