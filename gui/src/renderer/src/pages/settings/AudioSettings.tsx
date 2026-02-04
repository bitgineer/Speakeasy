/**
 * Audio Settings Page
 * 
 * Configuration for audio input device.
 */

import { useEffect } from 'react'
import { useSettingsStore } from '../../store'
import DeviceSelector from '../../components/DeviceSelector'

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
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Audio Settings</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Configure audio input device</p>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-3 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg flex items-center justify-between">
          <span className="text-[var(--color-error)] text-sm">{error}</span>
          <button onClick={clearError} className="text-[var(--color-error)] hover:opacity-80">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="space-y-6">
        {/* Audio Device Selection */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Input Device</h2>
          <DeviceSelector
            devices={availableDevices}
            selectedDevice={settings?.device_name || null}
            onChange={handleDeviceChange}
            disabled={isSaving}
          />
          <p className="mt-3 text-xs text-[var(--color-text-muted)]">
            Select the microphone or audio input device to use for transcription.
            Changes take effect immediately.
          </p>
        </section>

        {/* Audio Tips */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Tips for Best Results</h2>
          <ul className="space-y-2 text-sm text-[var(--color-text-secondary)]">
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Use a dedicated microphone for best audio quality</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Keep the microphone close to reduce background noise</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Speak clearly and at a moderate pace</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>Minimize background noise when recording</span>
            </li>
          </ul>
        </section>
      </div>
    </div>
  )
}
