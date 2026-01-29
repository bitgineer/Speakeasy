/**
 * Settings Page
 * 
 * Configuration page for model, device, hotkey, and other preferences.
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSettingsStore, useAppStore } from '../store'
import useDownloadStore from '../store/download-store'
import ModelSelector from '../components/ModelSelector'
import DeviceSelector from '../components/DeviceSelector'
import HotkeyInput from '../components/HotkeyInput'
import ModelDownloadDialog from '../components/ModelDownloadDialog'
import ExportDialog from '../components/ExportDialog'
import { SaveStatusIndicator } from '../components/SaveStatusIndicator'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
import { apiClient } from '../api/client'

export default function Settings(): JSX.Element {
  const navigate = useNavigate()
  
  const {
    settings,
    isLoading,
    isSaving,
    error,
    availableModels,
    availableDevices,
    needsModelReload,
    fetchSettings,
    fetchModels,
    fetchDevices,
    updateSettings,
    loadModel,
    setDevice,
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
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [importStatus, setImportStatus] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [mergeImport, setMergeImport] = useState(true)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Local state for form fields
  const [localSettings, setLocalSettings] = useState({
    model_type: '',
    model_name: '',
    device: 'cpu',
    compute_type: 'float16',
    language: 'auto',
    hotkey: '',
    hotkey_mode: 'toggle' as 'toggle' | 'push-to-talk',
    auto_paste: true,
    show_recording_indicator: true,
    enable_text_cleanup: false,
    custom_filler_words: ''
  })

  const [saveStatus, setSaveStatus] = useState<'idle' | 'unsaved' | 'saving' | 'saved'>('idle')
  const originalSettings = useRef(localSettings)

  // Handle keyboard shortcuts
  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === 'unsaved'
  })

  // Warn about unsaved changes
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent): void => {
      if (saveStatus === 'unsaved') {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [saveStatus])

  // Track unsaved changes
  useEffect(() => {
    const isDirty = JSON.stringify(localSettings) !== JSON.stringify(originalSettings.current)
    if (isDirty && saveStatus !== 'saving') {
      setSaveStatus('unsaved')
    } else if (!isDirty && saveStatus === 'unsaved') {
      setSaveStatus('idle')
    }
  }, [localSettings, saveStatus])
  
  // Fetch initial data
  useEffect(() => {
    fetchSettings()
    fetchModels()
    fetchDevices()
    fetchCacheInfo()
  }, [fetchSettings, fetchModels, fetchDevices, fetchCacheInfo])

  useEffect(() => {
    if (isDownloading) {
      setShowDownloadDialog(true)
    }
  }, [isDownloading])
  
  // Sync local state with fetched settings
  useEffect(() => {
    if (settings) {
      const newSettings = {
        model_type: settings.model_type,
        model_name: settings.model_name,
        device: settings.device,
        compute_type: settings.compute_type,
        language: settings.language,
        hotkey: settings.hotkey,
        hotkey_mode: settings.hotkey_mode || 'toggle',
        auto_paste: settings.auto_paste,
        show_recording_indicator: settings.show_recording_indicator,
        enable_text_cleanup: settings.enable_text_cleanup ?? false,
        custom_filler_words: settings.custom_filler_words?.join(', ') ?? ''
      }
      setLocalSettings(newSettings)
      originalSettings.current = newSettings
    }
  }, [settings])
  
  // Handle save
  const handleSave = async (): Promise<void> => {
    setSaveStatus('saving')
    const success = await updateSettings({
      model_type: localSettings.model_type,
      model_name: localSettings.model_name,
      device: localSettings.device,
      compute_type: localSettings.compute_type,
      language: localSettings.language,
      hotkey: localSettings.hotkey,
      hotkey_mode: localSettings.hotkey_mode,
      auto_paste: localSettings.auto_paste,
      show_recording_indicator: localSettings.show_recording_indicator,
      enable_text_cleanup: localSettings.enable_text_cleanup,
      custom_filler_words: localSettings.custom_filler_words
        ? localSettings.custom_filler_words.split(',').map(s => s.trim()).filter(Boolean)
        : null
    })
    
    if (success) {
      setSaveStatus('saved')
      originalSettings.current = localSettings
      
      if (localSettings.hotkey && window.api) {
        await window.api.registerHotkey(localSettings.hotkey)
      } else if (!localSettings.hotkey && window.api) {
        await window.api.unregisterHotkey()
      }
    } else {
      setSaveStatus('unsaved')
    }
  }
  
  // Handle model reload
  const handleLoadModel = async () => {
    await loadModel(localSettings.model_type, localSettings.model_name)
  }
  
  // Handle device change
  const handleDeviceChange = useCallback(async (deviceName: string) => {
    setLocalSettings(prev => ({ ...prev, device_name: deviceName }))
    await setDevice(deviceName)
  }, [setDevice])

  const handleTypeChange = useCallback((type: string) => {
    setLocalSettings(prev => ({ ...prev, model_type: type }))
  }, [])

  const handleNameChange = useCallback((name: string) => {
    setLocalSettings(prev => ({ ...prev, model_name: name }))
  }, [])

  // Handle import
  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsImporting(true)
    setImportStatus(null)

    try {
      const text = await file.text()
      const data = JSON.parse(text)

      if (!data.transcriptions || !Array.isArray(data.transcriptions)) {
        throw new Error('Invalid file format: missing "transcriptions" array')
      }

      const result = await apiClient.importHistory({
        data,
        merge: mergeImport
      })

      setImportStatus({
        message: `Successfully imported ${result.imported} records (skipped ${result.skipped})`,
        type: 'success'
      })
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      setImportStatus({
        message: err instanceof Error ? err.message : 'Import failed',
        type: 'error'
      })
    } finally {
      setIsImporting(false)
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-gray-600 border-t-blue-500 rounded-full animate-spin" />
      </div>
    )
  }
  
  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-xl font-semibold">Settings</h1>
        </div>
        <div className="flex items-center gap-4">
          <SaveStatusIndicator status={saveStatus} />
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn-primary"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="mb-6 p-3 bg-red-900/50 border border-red-700 rounded-lg flex items-center justify-between">
          <span className="text-red-300 text-sm">{error}</span>
          <button onClick={clearError} className="text-red-400 hover:text-red-300">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
      
      {/* Model reload warning */}
      {needsModelReload && (
        <div className="mb-6 p-3 bg-yellow-900/50 border border-yellow-700 rounded-lg flex items-center justify-between">
          <span className="text-yellow-300 text-sm">
            Model settings changed. Click "Load Model" to apply.
          </span>
          <button
            onClick={handleLoadModel}
            disabled={isSaving || isDownloading}
            className="btn-sm bg-yellow-600 text-white hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDownloading ? 'Downloading...' : 'Load Model'}
          </button>
        </div>
      )}
      
      <div className="space-y-8">
        {/* Model Settings */}
        <section className="card p-4">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Model Settings
          </h2>
          
          <ModelSelector
            availableModels={availableModels}
            selectedType={localSettings.model_type}
            selectedName={localSettings.model_name}
            onTypeChange={handleTypeChange}
            onNameChange={handleNameChange}
            disabled={isSaving}
          />
          
          {/* Device selection */}
          <div className="mt-4">
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
              <p className="mt-1 text-xs text-gray-500">
                GPU has {gpuVramGb.toFixed(1)}GB VRAM available
              </p>
            )}
          </div>
          
          {/* Compute type */}
          <div className="mt-4">
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
          <div className="mt-4">
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
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Downloaded Models
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm text-gray-400 bg-gray-800/50 p-3 rounded-lg border border-gray-700">
              <div className="flex flex-col">
                <span className="text-gray-300 font-medium">Local Cache Storage</span>
                <span className="text-xs text-gray-500 mt-1 font-mono break-all">{cacheDir || 'Loading...'}</span>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-white">{totalCacheSizeHuman || '0 B'}</div>
                <div className="text-xs text-gray-500">Total Usage</div>
              </div>
            </div>

            <div className="bg-gray-800/30 rounded-lg border border-gray-700 overflow-hidden">
              {cachedModels.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  No models downloaded yet.
                </div>
              ) : (
                <ul className="divide-y divide-gray-700">
                  {cachedModels.map((model) => (
                    <li key={model.model_name} className="p-3 flex items-center justify-between hover:bg-gray-700/30 transition-colors">
                      <div>
                        <div className="font-medium text-gray-200">{model.model_name}</div>
                        <div className="text-xs text-gray-500">{model.size_human} • {model.source}</div>
                      </div>
                      <button
                        onClick={() => {
                          if (confirm(`Are you sure you want to delete ${model.model_name}?`)) {
                            clearCache(model.model_name)
                          }
                        }}
                        disabled={isClearingCache}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
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
              <p className="text-xs text-gray-500">
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
                  className="text-xs text-red-400 hover:text-red-300 hover:underline disabled:opacity-50"
                >
                  {isClearingCache ? 'Clearing...' : 'Clear All Cache'}
                </button>
              )}
            </div>
          </div>
        </section>
        
        {/* Audio Settings */}
        <section className="card p-4">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            Audio Settings
          </h2>
          
          <DeviceSelector
            devices={availableDevices}
            selectedDevice={settings?.device_name || null}
            onChange={handleDeviceChange}
            disabled={isSaving}
          />
        </section>
        
        {/* Hotkey Settings */}
        <section className="card p-4">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            Hotkey Settings
          </h2>
          
          <HotkeyInput
            value={localSettings.hotkey}
            onChange={(hotkey) => setLocalSettings(prev => ({ ...prev, hotkey }))}
            disabled={isSaving}
          />
          
          <div className="mt-4">
            <label className="label">Hotkey Mode</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="hotkey_mode"
                  value="toggle"
                  checked={localSettings.hotkey_mode === 'toggle'}
                  onChange={() => setLocalSettings(prev => ({ ...prev, hotkey_mode: 'toggle' }))}
                  disabled={isSaving}
                  className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                />
                <div>
                  <span className="text-gray-100">Toggle</span>
                  <p className="text-xs text-gray-500">Press to start, press again to stop</p>
                </div>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="hotkey_mode"
                  value="push-to-talk"
                  checked={localSettings.hotkey_mode === 'push-to-talk'}
                  onChange={() => setLocalSettings(prev => ({ ...prev, hotkey_mode: 'push-to-talk' }))}
                  disabled={isSaving}
                  className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                />
                <div>
                  <span className="text-gray-100">Push-to-talk</span>
                  <p className="text-xs text-gray-500">Hold to record, release to stop</p>
                </div>
              </label>
            </div>
          </div>
        </section>
        
        {/* Behavior Settings */}
        <section className="card p-4">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Behavior
          </h2>
          
          <div className="space-y-4">
            {/* Auto-paste toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-gray-100">Auto-paste after transcription</span>
                <p className="text-xs text-gray-500 mt-0.5">
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
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
              </div>
            </label>
            
            {/* Recording indicator toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-gray-100">Show recording indicator</span>
                <p className="text-xs text-gray-500 mt-0.5">
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
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
              </div>
            </label>
          </div>
        </section>

        {/* Text Cleanup Settings */}
        <section className="card p-4">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Text Cleanup
          </h2>
          
          <div className="space-y-4">
            {/* Text cleanup toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <span className="text-gray-100">Remove filler words</span>
                <p className="text-xs text-gray-500 mt-0.5">
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
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
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

        {/* Data Management */}
        <section className="card p-4">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
            Data Management
          </h2>

          <div className="space-y-6">
            {/* Import */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-3">Import History</h3>
              <div className="flex flex-col gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={mergeImport}
                    onChange={(e) => setMergeImport(e.target.checked)}
                    disabled={isImporting}
                    className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-300">Merge with existing history</span>
                </label>
                
                <div className="flex items-center gap-3">
                  <input
                    type="file"
                    ref={fileInputRef}
                    accept=".json"
                    onChange={handleImport}
                    className="hidden"
                    disabled={isImporting}
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isImporting}
                    className="btn-secondary text-sm"
                  >
                    {isImporting ? 'Importing...' : 'Select JSON File'}
                  </button>
                  {importStatus && (
                    <span className={`text-sm ${importStatus.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                      {importStatus.message}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="border-t border-gray-700 pt-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Export History</h3>
              <button
                onClick={() => setShowExportDialog(true)}
                className="btn-secondary text-sm"
              >
                Export All History
              </button>
            </div>
          </div>
        </section>
        
        {/* About */}
        <section className="card p-4">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            About
          </h2>
          
          <div className="text-sm text-gray-400">
            <p className="mb-2">
              <strong className="text-gray-300">SpeakEasy</strong> - Open-source voice transcription
            </p>
            <p className="text-xs">
              Built with Electron, React, and FastAPI. Uses local ASR models for complete privacy.
            </p>
          </div>
        </section>
      </div>
      <ModelDownloadDialog 
        isOpen={showDownloadDialog} 
        onClose={() => setShowDownloadDialog(false)} 
      />
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
      />
    </div>
  )
}
