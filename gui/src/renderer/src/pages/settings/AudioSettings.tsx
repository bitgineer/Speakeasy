/**
 * Audio Settings Page
 * 
 * Configuration for audio input device.
 */

import { useEffect } from 'react'
import { Check, X } from 'lucide-react'
import { useSettingsStore } from '../../store'
import DeviceSelector from '../../components/DeviceSelector'

const AUDIO_TIPS = [
  'Use a dedicated microphone for best audio quality',
  'Keep the microphone close to reduce background noise',
  'Speak clearly and at a moderate pace',
  'Minimize background noise when recording'
]

export default function AudioSettings(): JSX.Element {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    availableDevices,
    fetchSettings,
    fetchDevices,
    setDevice,
    clearError
  } = useSettingsStore()

  useEffect(() => {
    fetchSettings()
    fetchDevices()
  }, [fetchSettings, fetchDevices])

  const handleDeviceChange = async (deviceName: string) => {
    await setDevice(deviceName)
  }

  if (isLoading) {
    return (
      <div className="workspace settings-loading">
        <span className="spinner animate-spin" role="status" aria-label="Loading audio settings" />
      </div>
    )
  }

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / audio</p>
          <h1>Audio Settings</h1>
          <p className="page-subtitle">Configure the audio input device.</p>
        </div>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button
            type="button"
            onClick={clearError}
            title="Dismiss error"
            aria-label="Dismiss error"
          >
            <X size={14} aria-hidden="true" />
          </button>
        </div>
      )}

      <div className="settings-stack">
        <section className="card settings-panel" aria-labelledby="input-device-title">
          <div className="settings-head">
            <h2 id="input-device-title">Input device</h2>
          </div>
          <DeviceSelector
            devices={availableDevices}
            selectedDevice={settings?.device_name || null}
            onChange={handleDeviceChange}
            disabled={isSaving}
          />
          <p className="settings-note">
            Select the microphone or audio input device to use for transcription. Changes take
            effect immediately.
          </p>
        </section>

        <section className="card settings-panel" aria-labelledby="audio-tips-title">
          <div className="settings-head">
            <h2 id="audio-tips-title">Tips for best results</h2>
          </div>
          <ul className="check-list">
            {AUDIO_TIPS.map((tip) => (
              <li key={tip}>
                <Check size={15} strokeWidth={2.25} aria-hidden="true" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
