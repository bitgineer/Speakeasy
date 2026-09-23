import { describe, expect, it } from 'vitest'
import {
  ACCENT_STORAGE_KEY,
  applyAppearance,
  readStoredAccent,
  resolveTheme,
  resolveThemeSetting,
  storeAccent
} from '../utils/theme'

const communityThemes = [
  'default',
  'tokyo-night',
  'catppuccin',
  'gruvbox',
  'everforest',
  'nord',
  'kanagawa',
  'ayu',
  'one-dark'
]

describe('theme setting resolution', () => {
  it('keeps the three explicit settings', () => {
    expect(resolveThemeSetting('light')).toBe('light')
    expect(resolveThemeSetting('dark')).toBe('dark')
    expect(resolveThemeSetting('system')).toBe('system')
  })

  it('renders every stored community theme name as Dark', () => {
    for (const name of communityThemes) {
      expect(resolveThemeSetting(name)).toBe('dark')
    }
  })

  it('renders unset values as Dark', () => {
    expect(resolveThemeSetting(null)).toBe('dark')
    expect(resolveThemeSetting(undefined)).toBe('dark')
    expect(resolveThemeSetting('')).toBe('dark')
  })

  it('resolves System through the media query result', () => {
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
    expect(resolveTheme('light', true)).toBe('light')
    expect(resolveTheme('dark', false)).toBe('dark')
  })

  it('applies both theme and accent to the document root', () => {
    applyAppearance('light', 'ink')
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(document.documentElement.dataset.accent).toBe('ink')

    applyAppearance('dark', 'violet')
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(document.documentElement.dataset.accent).toBe('violet')
  })

  it('round-trips the stored accent and defaults to violet', () => {
    window.localStorage.removeItem(ACCENT_STORAGE_KEY)
    expect(readStoredAccent()).toBe('violet')

    storeAccent('ink')
    expect(readStoredAccent()).toBe('ink')

    storeAccent('violet')
    expect(readStoredAccent()).toBe('violet')
  })
})
