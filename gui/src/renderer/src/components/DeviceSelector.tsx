/**
 * DeviceSelector Component
 * 
 * Dropdown for selecting audio input device.
 */

import { memo } from 'react'
import type { AudioDevice } from '../api/types'

interface DeviceSelectorProps {
  devices: AudioDevice[]
  selectedDevice: string | null
  onChange: (deviceName: string) => void
  disabled?: boolean
  isConnecting?: boolean
  error?: string | null
}

function DeviceSelector({
  devices,
  selectedDevice,
  onChange,
  disabled = false,
  isConnecting = false,
  error = null
}: DeviceSelectorProps): JSX.Element {
  return (
    <div>
      <div className="flex justify-between items-center">
        <label className="label">Audio Input Device</label>
        {isConnecting && (
          <div className="flex items-center text-xs text-[var(--color-info)] animate-pulse">
            <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-[var(--color-info)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Connecting...
          </div>
        )}
      </div>
      <select
        value={selectedDevice || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || devices.length === 0 || isConnecting}
        className={`select ${isConnecting ? 'opacity-50 pointer-events-none' : ''}`}
      >
        {devices.length === 0 ? (
          <option value="">No devices found</option>
        ) : (
          devices.map((device) => (
            <option key={device.id} value={device.name}>
              {device.name}
              {device.is_default ? ' (Default)' : ''}
            </option>
          ))
        )}
      </select>
      {error && (
        <p className="mt-1 text-xs text-[var(--color-error)] flex items-center">
          <span className="mr-1">x</span> {error}
        </p>
      )}
      {selectedDevice && (
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          {devices.find(d => d.name === selectedDevice)?.channels || 0} channel(s),{' '}
          {(devices.find(d => d.name === selectedDevice)?.sample_rate || 0) / 1000}kHz
        </p>
      )}
    </div>
  )
}

export default memo(DeviceSelector)
