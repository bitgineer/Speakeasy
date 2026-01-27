import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@renderer/test/utils'
import userEvent from '@testing-library/user-event'
import DeviceSelector from '../DeviceSelector'

describe('DeviceSelector', () => {
  const mockDevices = [
    { id: 'default', name: 'Default Microphone', is_default: true, channels: 2, sample_rate: 48000 },
    { id: 'usb-mic', name: 'USB Microphone', is_default: false, channels: 1, sample_rate: 44100 }
  ]

  const defaultProps = {
    devices: mockDevices,
    selectedDevice: 'Default Microphone',
    onChange: vi.fn(),
  }

  it('renders device dropdown correctly', () => {
    render(<DeviceSelector {...defaultProps} />)
    
    expect(screen.getByText('Audio Input Device')).toBeInTheDocument()
    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('Default Microphone')
  })

  it('displays available audio devices', () => {
    render(<DeviceSelector {...defaultProps} />)
    
    const select = screen.getByRole('combobox')
    const options = Array.from(select.children)
    
    expect(options).toHaveLength(2)
    expect(options[0]).toHaveTextContent('Default Microphone (Default)')
    expect(options[1]).toHaveTextContent('USB Microphone')
  })

  it('handles device selection', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<DeviceSelector {...defaultProps} onChange={onChange} />)
    
    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'USB Microphone')
    
    expect(onChange).toHaveBeenCalledWith('USB Microphone')
  })

  it('shows connecting state', () => {
    render(<DeviceSelector {...defaultProps} isConnecting={true} />)
    
    expect(screen.getByText('Connecting...')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeDisabled()
  })

  it('shows error message', () => {
    render(<DeviceSelector {...defaultProps} error="Device not found" />)
    
    expect(screen.getByText(/Device not found/)).toBeInTheDocument()
  })

  it('shows device details when selected', () => {
    render(<DeviceSelector {...defaultProps} />)
    
    // 48000 / 1000 = 48kHz
    expect(screen.getByText(/2 channel\(s\), 48kHz/)).toBeInTheDocument()
  })

  it('handles empty device list', () => {
    render(<DeviceSelector {...defaultProps} devices={[]} selectedDevice={null} />)
    
    const select = screen.getByRole('combobox')
    expect(select).toBeDisabled()
    expect(screen.getByText('No devices found')).toBeInTheDocument()
  })

  it('disables when disabled prop is true', () => {
    render(<DeviceSelector {...defaultProps} disabled={true} />)
    
    expect(screen.getByRole('combobox')).toBeDisabled()
  })
})
