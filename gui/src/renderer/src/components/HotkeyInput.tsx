/**
 * HotkeyInput Component
 * 
 * Input field for capturing keyboard shortcuts.
 */

import { useState, useRef, useEffect, useCallback } from 'react'

interface HotkeyInputProps {
  value: string
  onChange: (hotkey: string) => void
  disabled?: boolean
}

// Map key codes to display names
const keyDisplayNames: Record<string, string> = {
  ' ': 'Space',
  'ArrowUp': 'Up',
  'ArrowDown': 'Down',
  'ArrowLeft': 'Left',
  'ArrowRight': 'Right',
  'Escape': 'Esc',
  'Delete': 'Del',
  'Backspace': 'Backspace',
  'Enter': 'Enter',
  'Tab': 'Tab',
  'Home': 'Home',
  'End': 'End',
  'PageUp': 'PgUp',
  'PageDown': 'PgDn',
  'Insert': 'Ins',
  'Pause': 'Pause',
  'ScrollLock': 'ScrollLock',
  'PrintScreen': 'PrtSc',
  'ContextMenu': 'Menu',
}

function formatKeyForDisplay(key: string): string {
  // Check for special keys
  if (keyDisplayNames[key]) {
    return keyDisplayNames[key]
  }
  
  // Function keys
  if (key.startsWith('F') && !isNaN(parseInt(key.slice(1)))) {
    return key
  }
  
  // Single characters - uppercase
  if (key.length === 1) {
    return key.toUpperCase()
  }
  
  return key
}

function formatHotkeyForDisplay(hotkey: string): string {
  if (!hotkey) return ''
  
  // Split by + and format each part
  const parts = hotkey.split('+')
  return parts.map(part => {
    const trimmed = part.trim()
    if (trimmed === 'CommandOrControl') return 'Ctrl'
    if (trimmed === 'Command') return 'Cmd'
    if (trimmed === 'Control') return 'Ctrl'
    if (trimmed === 'Alt') return 'Alt'
    if (trimmed === 'Shift') return 'Shift'
    if (trimmed === 'Super') return 'Win'
    return formatKeyForDisplay(trimmed)
  }).join(' + ')
}

export default function HotkeyInput({
  value,
  onChange,
  disabled = false
}: HotkeyInputProps): JSX.Element {
  const [isCapturing, setIsCapturing] = useState(false)
  const [capturedKeys, setCapturedKeys] = useState<Set<string>>(new Set())
  const inputRef = useRef<HTMLInputElement>(null)
  
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!isCapturing) return
    
    e.preventDefault()
    e.stopPropagation()
    
    const key = e.key
    const newKeys = new Set(capturedKeys)
    
    // Add modifier keys
    if (e.ctrlKey) newKeys.add('Control')
    if (e.altKey) newKeys.add('Alt')
    if (e.shiftKey) newKeys.add('Shift')
    if (e.metaKey) newKeys.add('Super')
    
    // Add the main key (ignore if it's just a modifier)
    if (!['Control', 'Alt', 'Shift', 'Meta'].includes(key)) {
      newKeys.add(key)
    }
    
    setCapturedKeys(newKeys)
  }, [isCapturing, capturedKeys])
  
  const handleKeyUp = useCallback((e: KeyboardEvent) => {
    if (!isCapturing) return
    
    e.preventDefault()
    e.stopPropagation()
    
    // If we have at least one non-modifier key, save the hotkey
    const modifiers = ['Control', 'Alt', 'Shift', 'Super']
    const hasMainKey = Array.from(capturedKeys).some(k => !modifiers.includes(k))
    
    if (hasMainKey) {
      // Build the hotkey string in standard order
      const parts: string[] = []
      if (capturedKeys.has('Control')) parts.push('Control')
      if (capturedKeys.has('Alt')) parts.push('Alt')
      if (capturedKeys.has('Shift')) parts.push('Shift')
      if (capturedKeys.has('Super')) parts.push('Super')
      
      // Add the main key(s)
      capturedKeys.forEach(key => {
        if (!modifiers.includes(key)) {
          parts.push(key)
        }
      })
      
      const hotkeyString = parts.join('+')
      onChange(hotkeyString)
    }
    
    // Stop capturing
    setIsCapturing(false)
    setCapturedKeys(new Set())
    inputRef.current?.blur()
  }, [isCapturing, capturedKeys, onChange])
  
  useEffect(() => {
    if (isCapturing) {
      window.addEventListener('keydown', handleKeyDown, true)
      window.addEventListener('keyup', handleKeyUp, true)
      
      return () => {
        window.removeEventListener('keydown', handleKeyDown, true)
        window.removeEventListener('keyup', handleKeyUp, true)
      }
    }
  }, [isCapturing, handleKeyDown, handleKeyUp])
  
  const startCapturing = () => {
    if (disabled) return
    setIsCapturing(true)
    setCapturedKeys(new Set())
  }
  
  const clearHotkey = () => {
    onChange('')
    setIsCapturing(false)
    setCapturedKeys(new Set())
  }
  
  const displayValue = isCapturing
    ? capturedKeys.size > 0
      ? formatHotkeyForDisplay(Array.from(capturedKeys).join('+'))
      : 'Press keys...'
    : value
      ? formatHotkeyForDisplay(value)
      : 'Click to set hotkey'
  
  return (
    <div>
      <label className="label">Recording Hotkey</label>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={displayValue}
          onFocus={startCapturing}
          onBlur={() => {
            if (!capturedKeys.size) {
              setIsCapturing(false)
            }
          }}
          readOnly
          disabled={disabled}
          placeholder="Click to set hotkey"
          className={`input pr-20 cursor-pointer ${isCapturing ? 'ring-2 ring-blue-500' : ''}`}
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {value && !isCapturing && (
            <button
              type="button"
              onClick={clearHotkey}
              disabled={disabled}
              className="p-1 text-gray-500 hover:text-gray-300 disabled:opacity-50"
              title="Clear hotkey"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          {isCapturing && (
            <span className="text-xs text-blue-400 animate-pulse">Recording...</span>
          )}
        </div>
      </div>
      <p className="mt-1 text-xs text-gray-500">
        Click the input and press your desired key combination (e.g., F8, Ctrl+Shift+R)
      </p>
    </div>
  )
}
