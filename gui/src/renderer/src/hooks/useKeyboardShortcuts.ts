import { useEffect } from 'react'

interface ShortcutConfig {
  onSave?: () => void
  onEscape?: () => void
  onToggleRecording?: () => void
  enabled?: boolean
}

export function useKeyboardShortcuts(config: ShortcutConfig): void {
  const { onSave, onEscape, onToggleRecording, enabled = true } = config

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      const isInputElement =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement

      // Save shortcut: Ctrl/Cmd+S
      if ((event.metaKey || event.ctrlKey) && event.key === 's') {
        event.preventDefault()
        onSave?.()
        return
      }

      // Escape shortcut
      if (event.key === 'Escape') {
        event.preventDefault()
        onEscape?.()
        return
      }

      // Toggle recording: Space (only when not in input)
      if (event.key === ' ' && !isInputElement) {
        event.preventDefault()
        onToggleRecording?.()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [enabled, onSave, onEscape, onToggleRecording])
}
