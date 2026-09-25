/**
 * DeviceSelector Component
 *
 * Dropdown for selecting audio input device.
 */

import { memo } from 'react'
import { Loader2 } from 'lucide-react'
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
  const selected = devices.find((device) => device.name === selectedDevice)

  return (
    <div className="field">
      <div className="field-label-row">
        <label className="label" htmlFor="audio-input-device">
          Audio input device
        </label>
        {isConnecting && (
          <span className="field-status">
            <Loader2 className="animate-spin" size={12} aria-hidden="true" />
            Connecting...
          </span>
        )}
      </div>
      <select
        id="audio-input-device"
        value={selectedDevice || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || devices.length === 0 || isConnecting}
        className="select"
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
      {error && <p className="field-error">{error}</p>}
      {selectedDevice && (
        <p className="field-hint">
          {selected?.channels ?? 0} {selected?.channels === 1 ? 'channel' : 'channels'},{' '}
          {(selected?.sample_rate ?? 0) / 1000}kHz
        </p>
      )}
    </div>
  )
}

export default memo(DeviceSelector)
