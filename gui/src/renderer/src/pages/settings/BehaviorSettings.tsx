/**
 * Behavior Settings Page
 * 
 * Configuration for app behavior like auto-paste and text cleanup.
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import { useSettingsStore } from '../../store'
import { SaveStatusIndicator } from '../../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'

interface GrammarModelInfo {
  id: string
  name: string
  size_mb: number
  vram_gb: number
  description: string
  default: boolean
  downloaded: boolean
}

interface GrammarModelStatus {
  status: 'not_downloaded' | 'downloading' | 'downloaded' | 'loading' | 'loaded' | 'error'
  progress: number
  error: string | null
  active_model: string | null
}

interface GrammarModelsResponse {
  models: Record<string, GrammarModelInfo>
  current: {
    model_name: string
    device: string
    enabled: boolean
  } | null
  status: GrammarModelStatus
}

export default function BehaviorSettings(): JSX.Element {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    fetchSettings,
    updateSettings,
    clearError
  } = useSettingsStore()

  const [localSettings, setLocalSettings] = useState({
    auto_paste: true,
    show_recording_indicator: true,
    always_show_indicator: true,
    enable_text_cleanup: false,
    custom_filler_words: '',
    enable_grammar_correction: false,
    grammar_model: 'vennify/t5-base-grammar-correction',
    grammar_device: 'auto'
  })

  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const originalSettings = useRef(localSettings)
  
  // Grammar model state
  const [grammarModels, setGrammarModels] = useState<Record<string, GrammarModelInfo>>({})
  const [modelStatus, setModelStatus] = useState<GrammarModelStatus>({
    status: 'not_downloaded',
    progress: 0,
    error: null,
    active_model: null
  })
  const [isLoadingGrammarInfo, setIsLoadingGrammarInfo] = useState(false)
  const [isUnloadingModel, setIsUnloadingModel] = useState(false)
  const [isStartingDownload, setIsStartingDownload] = useState(false)

  // Fetch grammar model info
  const fetchGrammarModels = useCallback(async () => {
    // Don't set loading state if we're polling (status is downloading/loading)
    if (modelStatus.status !== 'downloading' && modelStatus.status !== 'loading') {
      setIsLoadingGrammarInfo(true)
    }
    
    try {
      const response = await fetch('http://127.0.0.1:8765/api/grammar/models')
      if (response.ok) {
        const data: GrammarModelsResponse = await response.json()
        setGrammarModels(data.models)
        setModelStatus(data.status)
      }
    } catch (err) {
      console.error('Failed to fetch grammar models:', err)
    } finally {
      setIsLoadingGrammarInfo(false)
    }
  }, [modelStatus.status])

  // Poll for status updates when downloading or loading
  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;
    
    if (modelStatus.status === 'downloading' || modelStatus.status === 'loading') {
      pollInterval = setInterval(fetchGrammarModels, 1000);
    }
    
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [modelStatus.status, fetchGrammarModels]);

  // Unload grammar model
  const handleUnloadModel = async (): Promise<void> => {
    setIsUnloadingModel(true)
    try {
      const response = await fetch('http://127.0.0.1:8765/api/grammar/unload', {
        method: 'POST'
      })
      if (response.ok) {
        await fetchGrammarModels()
      }
    } catch (err) {
      console.error('Failed to unload grammar model:', err)
    } finally {
      setIsUnloadingModel(false)
    }
  }

  // Trigger manual download
  const handleDownloadModel = async (): Promise<void> => {
    setIsStartingDownload(true)
    try {
      const response = await fetch('http://127.0.0.1:8765/api/grammar/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: localSettings.grammar_model })
      })
      
      if (response.ok) {
        // Fetch immediately to get the new status
        await fetchGrammarModels()
      }
    } catch (err) {
      console.error('Failed to start download:', err)
    } finally {
      setIsStartingDownload(false)
    }
  }

  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  useEffect(() => {
    const isDirty = JSON.stringify(localSettings) !== JSON.stringify(originalSettings.current)
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [localSettings, saveStatus])

  useEffect(() => {
    fetchSettings()
    fetchGrammarModels()
  }, []) // Remove dependencies to prevent infinite loop
  
  // Set local settings when settings are loaded
  useEffect(() => {
    if (settings) {
      const newSettings = {
        auto_paste: settings.auto_paste,
        show_recording_indicator: settings.show_recording_indicator,
        always_show_indicator: settings.always_show_indicator ?? true,
        enable_text_cleanup: settings.enable_text_cleanup ?? false,
        custom_filler_words: settings.custom_filler_words?.join(', ') ?? '',
        enable_grammar_correction: settings.enable_grammar_correction ?? false,
        grammar_model: settings.grammar_model ?? 'vennify/t5-base-grammar-correction',
        grammar_device: settings.grammar_device ?? 'auto'
      }
      
      // Only update if we haven't modified local settings yet (initial load)
      // or if we just saved
      if (saveStatus === 'idle' || saveStatus === 'saved') {
        setLocalSettings(newSettings)
        originalSettings.current = newSettings
      }
    }
  }, [settings, saveStatus])

  const handleSave = async (): Promise<void> => {
    setSaveStatus('saving')
    const success = await updateSettings({
      auto_paste: localSettings.auto_paste,
      show_recording_indicator: localSettings.show_recording_indicator,
      always_show_indicator: localSettings.always_show_indicator,
      enable_text_cleanup: localSettings.enable_text_cleanup,
      custom_filler_words: localSettings.custom_filler_words
        ? localSettings.custom_filler_words.split(',').map(s => s.trim()).filter(Boolean)
        : null,
      enable_grammar_correction: localSettings.enable_grammar_correction,
      grammar_model: localSettings.grammar_model,
      grammar_device: localSettings.grammar_device
    })

    if (success) {
      setSaveStatus('saved')
      originalSettings.current = localSettings
    } else {
      setSaveStatus('unsaved')
    }
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Behavior</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Configure app behavior and text processing</p>
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

      <div className="space-y-6">
        {/* Recording Behavior */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Recording Behavior</h2>
          
          <div className="space-y-4">
            {/* Auto-paste toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-[var(--color-text-primary)]">Auto-paste after transcription</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Automatically paste transcribed text to the active window
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={localSettings.auto_paste}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, auto_paste: e.target.checked }))}
                  disabled={isSaving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
              </div>
            </label>
            
            {/* Recording indicator toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-[var(--color-text-primary)]">Show recording indicator</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Display a visual indicator in the center of the screen while recording
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={localSettings.show_recording_indicator}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, show_recording_indicator: e.target.checked }))}
                  disabled={isSaving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
              </div>
            </label>

            {/* Always show indicator toggle */}
            <div className={`transition-all duration-300 overflow-hidden ${localSettings.show_recording_indicator ? 'max-h-20 opacity-100' : 'max-h-0 opacity-0'}`}>
              <label className="flex items-center justify-between cursor-pointer ml-6 pl-4 border-l-2 border-[var(--color-border)] mt-4">
                <div>
                  <span className="text-[var(--color-text-primary)]">Always show "Ready" status</span>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    Keep the indicator visible on screen when idle
                  </p>
                </div>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={localSettings.always_show_indicator}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, always_show_indicator: e.target.checked }))}
                    disabled={isSaving}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
                </div>
              </label>
            </div>
          </div>
        </section>

        {/* Text Cleanup */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Text Cleanup</h2>
          
          <div className="space-y-4">
            {/* Text cleanup toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-[var(--color-text-primary)]">Remove filler words</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Automatically remove common filler words like "um", "uh", "like", etc.
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={localSettings.enable_text_cleanup}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, enable_text_cleanup: e.target.checked }))}
                  disabled={isSaving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
              </div>
            </label>

            {/* Custom filler words input */}
            {localSettings.enable_text_cleanup && (
              <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                <label className="label">Additional filler words (comma-separated)</label>
                <input
                  type="text"
                  value={localSettings.custom_filler_words}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, custom_filler_words: e.target.value }))}
                  disabled={isSaving}
                  placeholder="e.g., basically, literally, actually"
                  className="input w-full"
                />
              </div>
            )}
          </div>
        </section>

        {/* Grammar Correction */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Grammar Correction</h2>

          <div className="space-y-4">
            {/* Grammar correction toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-[var(--color-text-primary)]">Enable AI grammar correction</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Use a local AI model to fix grammar and improve fluency
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={localSettings.enable_grammar_correction}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, enable_grammar_correction: e.target.checked }))}
                  disabled={isSaving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" />
              </div>
            </label>

            {/* Grammar model selector */}
            {localSettings.enable_grammar_correction && (
              <div className="animate-in fade-in slide-in-from-top-2 duration-200 space-y-4">
                {/* Model selector */}
                <div>
                  <label className="label">Grammar Model</label>
                  <select
                    value={localSettings.grammar_model}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, grammar_model: e.target.value }))}
                    disabled={isSaving}
                    className="input w-full"
                  >
                    {Object.entries(grammarModels).length > 0 ? (
                      Object.entries(grammarModels).map(([id, model]) => (
                        <option key={id} value={id}>
                          {model.name} ({model.size_mb}MB){model.downloaded ? ' ✓' : ''}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="vennify/t5-base-grammar-correction">
                          T5 Base Grammar Correction (890MB, recommended)
                        </option>
                        <option value="google/flan-t5-small">
                          Google Flan T5 Small (300MB, CPU friendly)
                        </option>
                        <option value="google/flan-t5-base">
                          Google Flan T5 Base (990MB)
                        </option>
                        <option value="pszemraj/flan-t5-large-grammar-synthesis">
                          Flan T5 Large Grammar Synthesis (3GB)
                        </option>
                        <option value="grammarly/coedit-xl">
                          Grammarly CoEdit XL (3GB, high quality)
                        </option>
                      </>
                    )}
                  </select>
                </div>

                {/* Model status info */}
                {grammarModels[localSettings.grammar_model] && (
                  <div className="p-3 bg-[var(--color-bg-secondary)] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-[var(--color-text-primary)]">
                        {grammarModels[localSettings.grammar_model].name}
                      </span>
                      <div className="flex items-center gap-2">
                        {grammarModels[localSettings.grammar_model].downloaded ? (
                          <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full">
                            Downloaded
                          </span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded-full">
                            Will download on first use
                          </span>
                        )}
                        {modelStatus.active_model === localSettings.grammar_model && (
                          <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full">
                            Loaded
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {grammarModels[localSettings.grammar_model].description}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-[var(--color-text-muted)]">
                      <span>Size: {grammarModels[localSettings.grammar_model].size_mb}MB</span>
                      <span>VRAM: ~{grammarModels[localSettings.grammar_model].vram_gb}GB</span>
                    </div>

                    {/* Unload button */}
                    {modelStatus.active_model === localSettings.grammar_model && modelStatus.status === 'loaded' && (
                      <button
                        onClick={handleUnloadModel}
                        disabled={isUnloadingModel}
                        className="mt-3 px-3 py-1.5 text-xs bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-border)] text-[var(--color-text-secondary)] rounded transition-colors"
                      >
                        {isUnloadingModel ? 'Unloading...' : `Unload Model (Free VRAM)`}
                      </button>
                    )}
                    
                    {/* Download button */}
                    {!grammarModels[localSettings.grammar_model].downloaded && 
                     modelStatus.status !== 'downloading' && 
                     modelStatus.status !== 'loading' && (
                      <button
                        onClick={handleDownloadModel}
                        disabled={isStartingDownload}
                        className="mt-3 px-3 py-1.5 text-xs bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded transition-colors"
                      >
                        {isStartingDownload ? 'Starting...' : `Download Model Now`}
                      </button>
                    )}
                    
                    {/* Progress Bar */}
                    {(modelStatus.status === 'downloading' || modelStatus.status === 'loading') && (
                      <div className="mt-3 space-y-1">
                        <div className="flex justify-between text-xs text-[var(--color-text-secondary)]">
                          <span>{modelStatus.status === 'downloading' ? 'Downloading...' : 'Loading...'}</span>
                          <span>{Math.round(modelStatus.progress * 100)}%</span>
                        </div>
                        <div className="w-full bg-[var(--color-bg-tertiary)] rounded-full h-1.5 overflow-hidden">
                          <div 
                            className="bg-[var(--color-accent)] h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${modelStatus.progress * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* Error Message */}
                    {modelStatus.status === 'error' && modelStatus.error && (
                      <div className="mt-3 p-2 bg-red-500/10 text-red-500 text-xs rounded border border-red-500/20">
                        Error: {modelStatus.error}
                      </div>
                    )}
                  </div>
                )}

                {/* Loading state for grammar info */}
                {isLoadingGrammarInfo && !Object.keys(grammarModels).length && (
                  <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
                    <div className="w-4 h-4 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
                    Loading model info...
                  </div>
                )}

                {/* Device selector */}
                <div>
                  <label className="label">Device</label>
                  <select
                    value={localSettings.grammar_device}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, grammar_device: e.target.value }))}
                    disabled={isSaving}
                    className="input w-full"
                  >
                    <option value="auto">Auto (GPU if available, otherwise CPU)</option>
                    <option value="cuda">GPU (CUDA)</option>
                    <option value="cpu">CPU</option>
                  </select>
                  <p className="text-xs text-[var(--color-text-muted)] mt-1.5">
                    GPU is faster but requires a compatible graphics card with sufficient VRAM.
                  </p>
                </div>

                {/* Info note */}
                <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <p className="text-xs text-blue-400">
                    <strong>Note:</strong> The model will download automatically on first use. 
                    This may take a moment depending on your internet speed. The model runs locally 
                    on your device for privacy.
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
