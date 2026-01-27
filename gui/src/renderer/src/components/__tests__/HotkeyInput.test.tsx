import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@renderer/test/utils'
import HotkeyInput from '../HotkeyInput'

describe('HotkeyInput', () => {
  const defaultProps = {
    value: 'Control+Shift+Space',
    onChange: vi.fn(),
  }

  it('renders hotkey input correctly', () => {
    render(<HotkeyInput {...defaultProps} />)
    
    expect(screen.getByText('Recording Hotkey')).toBeInTheDocument()
    // The component formats keys with spaces around +
    expect(screen.getByDisplayValue('Ctrl + Shift + Space')).toBeInTheDocument()
  })

  it('displays current hotkey value', () => {
    render(<HotkeyInput {...defaultProps} value="Alt+F4" />)
    
    expect(screen.getByDisplayValue('Alt + F4')).toBeInTheDocument()
  })

  it('starts capturing on focus', () => {
    render(<HotkeyInput {...defaultProps} />)
    
    const input = screen.getByRole('textbox')
    fireEvent.focus(input)
    
    expect(screen.getByText('Recording...')).toBeInTheDocument()
  })

  it('captures keyboard shortcuts', () => {
    const onChange = vi.fn()
    render(<HotkeyInput {...defaultProps} onChange={onChange} />)
    
    const input = screen.getByRole('textbox')
    fireEvent.focus(input)
    
    // Simulate pressing keys
    // Note: We need to fire on window because the component attaches listeners to window
    fireEvent.keyDown(window, { key: 'Control', ctrlKey: true })
    fireEvent.keyDown(window, { key: 'Shift', shiftKey: true, ctrlKey: true })
    fireEvent.keyDown(window, { key: 'a', shiftKey: true, ctrlKey: true })
    
    // Release keys to trigger change
    fireEvent.keyUp(window, { key: 'a', shiftKey: true, ctrlKey: true })
    
    expect(onChange).toHaveBeenCalledWith('Control+Shift+a')
    expect(screen.queryByText('Recording...')).not.toBeInTheDocument()
  })

  it('handles clear button', () => {
    const onChange = vi.fn()
    render(<HotkeyInput {...defaultProps} onChange={onChange} />)
    
    const clearButton = screen.getByTitle('Clear hotkey')
    fireEvent.click(clearButton)
    
    expect(onChange).toHaveBeenCalledWith('')
  })

  it('stops capturing on blur without change if no keys pressed', () => {
    render(<HotkeyInput {...defaultProps} />)
    
    const input = screen.getByRole('textbox')
    fireEvent.focus(input)
    expect(screen.getByText('Recording...')).toBeInTheDocument()
    
    fireEvent.blur(input)
    expect(screen.queryByText('Recording...')).not.toBeInTheDocument()
  })

  it('disables input when disabled prop is true', () => {
    render(<HotkeyInput {...defaultProps} disabled={true} />)
    
    const input = screen.getByRole('textbox')
    expect(input).toBeDisabled()
    
    const clearButton = screen.getByTitle('Clear hotkey')
    expect(clearButton).toBeDisabled()
  })
})
