/**
 * Model Settings Page
 * 
 * Configuration for transcription model, device, and compute settings.
 * Models are fetched on-demand via Sync button to improve performance.
 */

import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, Trash2, X } from 'lucide-react'
import { useSettingsStore, useAppStore } from '../../store'
import useDownloadStore from '../../store/download-store'
import ModelSelector from '../../components/ModelSelector'
import ModelDownloadDialog from '../../components/ModelDownloadDialog'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { Button } from '../../components/ui/button'

type ModelDraft = {
  model_type: string
  model_name: string
  device: 'cuda' | 'cpu'
  compute_type: string
  language: string
}

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
  const [localSettings, setLocalSettings] = useState<ModelDraft>({
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
      <div className="workspace settings-loading">
        <span className="spinner animate-spin" role="status" aria-label="Loading model settings" />
      </div>
    )
  }

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / model</p>
          <h1>Model settings</h1>
          <p className="page-subtitle">Configure the transcription model and performance.</p>
        </div>
        <div className="page-actions">
          <SaveStatusIndicator status={saveStatus} />
          <Button
            onClick={handleSave}
            disabled={isSaving || saveStatus === 'idle' || saveStatus === 'saved'}
          >
            {isSaving ? 'Saving...' : 'Save changes'}
          </Button>
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

      {needsModelReload && (
        <div className="warning-banner" role="status">
          <span>Model settings changed. Select &quot;Load model&quot; to apply.</span>
          <Button size="sm" onClick={handleLoadModel} disabled={isSaving || isDownloading}>
            {isDownloading ? 'Downloading...' : 'Load model'}
          </Button>
        </div>
      )}

      <div className="settings-stack">
        {/* Model Selection */}
        <section className="card settings-panel" aria-labelledby="model-selection-title">
          <div className="settings-head">
            <h2 id="model-selection-title">Model selection</h2>
          </div>
          
          {Object.keys(availableModels).length === 0 ? (
            <div className="settings-loading">
              <span
                className="spinner animate-spin"
                role="status"
                aria-label="Loading available models"
              />
              <p className="panel-subtitle">Loading available models...</p>
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
        <section className="card settings-panel" aria-labelledby="compute-settings-title">
          <div className="settings-head">
            <h2 id="compute-settings-title">Compute settings</h2>
          </div>
          
          <div className="field-grid">
            <div className="field field-wide">
              <label className="label" htmlFor="compute-device">
                Compute device
              </label>
              <select
                id="compute-device"
                value={localSettings.device}
                onChange={(e) =>
                  setLocalSettings(prev => ({ ...prev, device: e.target.value as 'cuda' | 'cpu' }))
                }
                disabled={isSaving}
                className="select"
              >
                <option value="cpu">CPU</option>
                <option value="cuda" disabled={!gpuAvailable}>
                  GPU (CUDA){gpuAvailable ? ` - ${gpuName}` : ' - Not available'}
                </option>
              </select>
              {gpuAvailable && gpuVramGb && (
                <p className="field-hint">GPU has {gpuVramGb.toFixed(1)}GB VRAM available</p>
              )}
            </div>

            <div className="field">
              <label className="label" htmlFor="compute-precision">
                Compute precision
              </label>
              <select
                id="compute-precision"
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

            <div className="field">
              <label className="label" htmlFor="compute-language">
                Language
              </label>
              <select
                id="compute-language"
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
          </div>
        </section>

        {/* Downloaded Models */}
        <section className="card settings-panel" aria-labelledby="downloaded-models-title">
          <div className="settings-head">
            <h2 id="downloaded-models-title">Downloaded models</h2>
            <div className="input-row">
              {lastSyncTime && (
                <span className="muted text-caption">
                  Last synced: {lastSyncTime.toLocaleTimeString()}
                </span>
              )}
              <Button variant="secondary" size="sm" onClick={handleSyncModels} disabled={isSyncing}>
                <RefreshCw
                  size={14}
                  className={isSyncing ? 'animate-spin' : undefined}
                  aria-hidden="true"
                />
                {isSyncing ? 'Syncing...' : 'Refresh'}
              </Button>
            </div>
          </div>
          
          <div className="settings-rows">
            <div className="subpanel">
              <div className="cache-meta">
                <div>
                  <span className="switch-label">Local cache storage</span>
                  <div className="cache-path">{cacheDir || 'Loading...'}</div>
                </div>
                <div>
                  <div className="cache-size">{totalCacheSizeHuman || '0 B'}</div>
                  <div className="cache-size-label">Total usage</div>
                </div>
              </div>
            </div>

            {cachedModels.length === 0 ? (
              <p className="empty-panel">
                No models downloaded yet. Models download when you load them.
              </p>
            ) : (
              <ul className="file-list">
                {cachedModels.map((model) => (
                  <li key={model.model_name} className="file-row model-row">
                    <span className="file-text">
                      <span className="file-name">{model.model_name}</span>
                      <span className="queue-size">
                        {model.size_human} · {model.source}
                      </span>
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        if (confirm(`Delete ${model.model_name}? This cannot be undone.`)) {
                          clearCache(model.model_name)
                        }
                      }}
                      disabled={isClearingCache}
                      className="icon-button"
                      data-tone="danger"
                      title="Delete model"
                      aria-label={`Delete ${model.model_name}`}
                    >
                      <Trash2 size={15} aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <div className="settings-foot">
              <p className="panel-subtitle">
                Models are cached locally to enable offline use and faster loading.
              </p>
              {cachedModels.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    if (confirm('Delete all downloaded models? This cannot be undone.')) {
                      clearCache()
                    }
                  }}
                  disabled={isClearingCache}
                  className="text-button"
                  data-tone="danger"
                >
                  {isClearingCache ? 'Clearing...' : 'Clear all cached models'}
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
