/**
 * Model Settings Page
 * 
 * Configuration for transcription model, device, and compute settings.
 * Models are fetched on-demand via Sync button to improve performance.
 */

import { useEffect, useState, useCallback } from 'react'
import { useSettingsStore, useAppStore } from '../../store'
import useDownloadStore from '../../store/download-store'
import ModelSelector from '../../components/ModelSelector'
import ModelDownloadDialog from '../../components/ModelDownloadDialog'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'

export default function ModelSettings(): JSX.Element {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    availableModels,
    needsModelReload,
    fetchSettings,
    fetchModels,
    updateSettings,
    loadModel,
    clearError
  } = useSettingsStore()
  
  const { gpuAvailable, gpuName, gpuVramGb } = useAppStore()
  
  const { 
    isDownloading, 
    cachedModels, 
    cacheDir, 
    totalCacheSizeHuman, 
    fetchCacheInfo, 
    clearCache, 
    isClearingCache 
  } = useDownloadStore()

  const [showDownloadDialog, setShowDownloadDialog] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null)
  const [localSettings, setLocalSettings] = useState({
    model_type: '',
    model_name: '',
    device: 'cpu',
    compute_type: 'float16',
    language: 'auto'
  })

  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const [originalSettings, setOriginalSettings] = useState(localSettings)

  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  // Track unsaved changes
  useEffect(() => {
    const isDirty = JSON.stringify(localSettings) !== JSON.stringify(originalSettings)
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [localSettings, saveStatus, originalSettings])

  // Fetch settings, available models, and cached models on mount
  useEffect(() => {
    fetchSettings()
    fetchModels() // Auto-fetch available models for dropdowns
    fetchCacheInfo() // Auto-fetch cached models for display
  }, [fetchSettings, fetchModels, fetchCacheInfo])

  useEffect(() => {
    if (isDownloading) {
      setShowDownloadDialog(true)
    }
  }, [isDownloading])

  useEffect(() => {
    if (settings) {
      const newSettings = {
        model_type: settings.model_type,
        model_name: settings.model_name,
        device: settings.device,
        compute_type: settings.compute_type,
        language: settings.language
      }
      setLocalSettings(newSettings)
      setOriginalSettings(newSettings)
    }
  }, [settings])

  // Manual sync function for fetching downloaded models status
  const handleSyncModels = useCallback(async () => {
    setIsSyncing(true)
    try {
      await fetchCacheInfo() // Only sync downloaded models status
      setLastSyncTime(new Date())
    } finally {
      setIsSyncing(false)
    }
  }, [fetchCacheInfo])

  const handleSave = async (): Promise<void> => {
    setSaveStatus('saving')
    const success = await updateSettings({
      model_type: localSettings.model_type,
      model_name: localSettings.model_name,
      device: localSettings.device,
      compute_type: localSettings.compute_type,
      language: localSettings.language
    })
    
    if (success) {
      setSaveStatus('saved')
      setOriginalSettings(localSettings)
    } else {
      setSaveStatus('unsaved')
    }
  }

  const handleLoadModel = async () => {
    await loadModel(localSettings.model_type, localSettings.model_name)
  }

  const handleTypeChange = useCallback((type: string) => {
    setLocalSettings(prev => ({ ...prev, model_type: type }))
  }, [])

  const handleNameChange = useCallback((name: string) => {
    setLocalSettings(prev => ({ ...prev, model_name: name }))
  }, [])

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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Model Settings</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Configure transcription model and performance</p>
        </div>
        <div className="flex items-center gap-4">
          <SaveStatusIndicator status={saveStatus} />
          <button
            onClick={handleSave}
            disabled={isSaving || saveStatus === 'idle' || saveStatus === 'saved'}
            className="btn-primary"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
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

      {/* Model reload warning */}
      {needsModelReload && (
        <div className="mb-6 p-3 bg-[var(--color-warning-muted)] border border-[var(--color-warning)] rounded-lg flex items-center justify-between">
          <span className="text-[var(--color-warning)] text-sm">
            Model settings changed. Click "Load Model" to apply.
          </span>
          <button
            onClick={handleLoadModel}
            disabled={isSaving || isDownloading}
            className="btn-sm bg-[var(--color-warning)] text-[var(--color-bg-primary)] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDownloading ? 'Downloading...' : 'Load Model'}
          </button>
        </div>
      )}

      <div className="space-y-6">
        {/* Model Selection */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Model Selection</h2>
          
          {availableModels.length === 0 ? (
            <div className="text-center py-8 text-[var(--color-text-muted)]">
              <div className="w-6 h-6 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm">Loading available models...</p>
            </div>
          ) : (
            <ModelSelector
              availableModels={availableModels}
              selectedType={localSettings.model_type}
              selectedName={localSettings.model_name}
              onTypeChange={handleTypeChange}
              onNameChange={handleNameChange}
              disabled={isSaving}
            />
          )}
        </section>

        {/* Compute Settings */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Compute Settings</h2>
          
          {/* Device selection */}
          <div className="mb-4">
            <label className="label">Compute Device</label>
            <select
              value={localSettings.device}
              onChange={(e) => setLocalSettings(prev => ({ ...prev, device: e.target.value }))}
              disabled={isSaving}
              className="select"
            >
              <option value="cpu">CPU</option>
              <option value="cuda" disabled={!gpuAvailable}>
                GPU (CUDA){gpuAvailable ? ` - ${gpuName}` : ' - Not available'}
              </option>
            </select>
            {gpuAvailable && gpuVramGb && (
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                GPU has {gpuVramGb.toFixed(1)}GB VRAM available
              </p>
            )}
          </div>

          {/* Compute type */}
          <div className="mb-4">
            <label className="label">Compute Precision</label>
            <select
              value={localSettings.compute_type}
              onChange={(e) => setLocalSettings(prev => ({ ...prev, compute_type: e.target.value }))}
              disabled={isSaving}
              className="select"
            >
              <option value="float32">Float32 (Most accurate, slowest)</option>
              <option value="float16">Float16 (Balanced)</option>
              <option value="int8">Int8 (Fastest, less accurate)</option>
            </select>
          </div>

          {/* Language */}
          <div>
            <label className="label">Language</label>
            <select
              value={localSettings.language}
              onChange={(e) => setLocalSettings(prev => ({ ...prev, language: e.target.value }))}
              disabled={isSaving}
              className="select"
            >
              <option value="auto">Auto-detect</option>
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="pt">Portuguese</option>
              <option value="nl">Dutch</option>
              <option value="ja">Japanese</option>
              <option value="ko">Korean</option>
              <option value="zh">Chinese</option>
              <option value="ru">Russian</option>
              <option value="ar">Arabic</option>
              <option value="hi">Hindi</option>
            </select>
          </div>
        </section>

        {/* Downloaded Models */}
        <section className="card p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-medium text-[var(--color-text-primary)]">Downloaded Models</h2>
            <div className="flex items-center gap-3">
              {lastSyncTime && (
                <span className="text-xs text-[var(--color-text-muted)]">
                  Last synced: {lastSyncTime.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={handleSyncModels}
                disabled={isSyncing}
                className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg transition-colors border border-[var(--color-border)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg 
                  className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {isSyncing ? 'Syncing...' : 'Refresh'}
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm text-[var(--color-text-muted)] bg-[var(--color-bg-tertiary)] p-3 rounded-lg border border-[var(--color-border)]">
              <div className="flex flex-col">
                <span className="text-[var(--color-text-secondary)] font-medium">Local Cache Storage</span>
                <span className="text-xs text-[var(--color-text-muted)] mt-1 font-mono break-all">{cacheDir || 'Loading...'}</span>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-[var(--color-text-primary)]">{totalCacheSizeHuman || '0 B'}</div>
                <div className="text-xs text-[var(--color-text-muted)]">Total Usage</div>
              </div>
            </div>

            <div className="bg-[var(--color-bg-tertiary)] rounded-lg border border-[var(--color-border)] overflow-hidden">
              {cachedModels.length === 0 ? (
                <div className="p-4 text-center text-[var(--color-text-muted)] text-sm">
                  No models downloaded yet.
                </div>
              ) : (
                <ul className="divide-y divide-[var(--color-border)]">
                  {cachedModels.map((model) => (
                    <li key={model.model_name} className="p-3 flex items-center justify-between hover:bg-[var(--color-bg-elevated)] transition-colors">
                      <div>
                        <div className="font-medium text-[var(--color-text-secondary)]">{model.model_name}</div>
                        <div className="text-xs text-[var(--color-text-muted)]">{model.size_human} • {model.source}</div>
                      </div>
                      <button
                        onClick={() => {
                          if (confirm(`Are you sure you want to delete ${model.model_name}?`)) {
                            clearCache(model.model_name)
                          }
                        }}
                        disabled={isClearingCache}
                        className="p-2 text-[var(--color-text-muted)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-muted)] rounded-lg transition-colors"
                        title="Delete model"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="flex items-center justify-between pt-2">
              <p className="text-xs text-[var(--color-text-muted)]">
                Models are cached locally to enable offline use and faster loading.
              </p>
              {cachedModels.length > 0 && (
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete ALL downloaded models? This cannot be undone.')) {
                      clearCache()
                    }
                  }}
                  disabled={isClearingCache}
                  className="text-xs text-[var(--color-error)] hover:opacity-80 disabled:opacity-50"
                >
                  {isClearingCache ? 'Clearing...' : 'Clear All Cache'}
                </button>
              )}
            </div>
          </div>
        </section>
      </div>

      <ModelDownloadDialog 
        isOpen={showDownloadDialog} 
        onClose={() => setShowDownloadDialog(false)} 
      />
    </div>
  )
}
