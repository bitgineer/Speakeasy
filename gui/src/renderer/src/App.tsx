/**
 * App Root Component
 * 
 * Sets up routing and global providers.
 * Uses HashRouter required for Electron file:// protocol.
 */

import { useEffect, lazy, Suspense } from 'react'
import { HashRouter, Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAppStore, useHistoryStore, useSettingsStore, initHistoryWebSocket } from './store'
import { configureBackendPort } from './api/backend-port'
import ErrorBoundary from './components/ErrorBoundary'
import LoadingSpinner from './components/LoadingSpinner'
import Sidebar from './components/Sidebar'
import { resolveRoute } from './utils/navigation'
import { ToastProvider } from './context/ToastProvider'
import { useHotkeyRegistration, useToast } from './hooks'
import type { HotkeyBinding, HotkeyRegistrationResult, TranscriptionRecord } from './api/types'
import type { MessageBoxOptions, MessageBoxReturnValue } from 'electron'
import {
  applyAppearance,
  readStoredAccent,
  resolveTheme,
  resolveThemeSetting,
  useSystemPrefersDark
} from './utils/theme'

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'))
const BatchTranscription = lazy(() => import('./pages/BatchTranscription'))
const Stats = lazy(() => import('./pages/Stats'))
const RecordingIndicator = lazy(() => import('./components/RecordingIndicator'))

// Settings pages
const ModelSettings = lazy(() => import('./pages/settings/ModelSettings'))
const AudioSettings = lazy(() => import('./pages/settings/AudioSettings'))
const HotkeySettings = lazy(() => import('./pages/settings/HotkeySettings'))
const ProcessingSettings = lazy(() => import('./pages/settings/ProcessingSettings'))
const BehaviorSettings = lazy(() => import('./pages/settings/BehaviorSettings'))
const AppearanceSettings = lazy(() => import('./pages/settings/AppearanceSettings'))
const DataSettings = lazy(() => import('./pages/settings/DataSettings'))
const AboutSettings = lazy(() => import('./pages/settings/AboutSettings'))

// Navigation listener component
function NavigationListener(): null {
  const navigate = useNavigate()
  const location = useLocation()
  
  useEffect(() => {
    // Listen for navigation events from main process
    const unsubscribe = window.api?.onNavigate((path: string) => {
      if (path !== location.pathname) {
        navigate(path)
      }
    })
    
    return () => {
      unsubscribe?.()
    }
  }, [navigate, location.pathname])
  
  return null
}

// Theme initializer - applies Light, Dark, or the resolved System setting
function ThemeInitializer(): null {
  const { settings, fetchSettings } = useSettingsStore()
  const systemPrefersDark = useSystemPrefersDark()
  
  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])
  
  useEffect(() => {
    const theme = resolveTheme(resolveThemeSetting(settings?.theme), systemPrefersDark)
    applyAppearance(theme, readStoredAccent())
  }, [settings?.theme, systemPrefersDark])
  
  return null
}

// Topbar shown above every main-window page: breadcrumb on the left, the live
// recording and model status on the right.
function Topbar(): JSX.Element {
  const { pathname } = useLocation()
  const { isRecording, modelLoaded, modelLoading, modelName } = useAppStore()
  const { group, title } = resolveRoute(pathname)

  const status = isRecording
    ? { tone: 'danger', label: 'Recording' }
    : modelLoading
      ? { tone: 'warning', label: 'Loading model...' }
      : modelLoaded
        ? { tone: 'success', label: 'Ready' }
        : { tone: 'warning', label: 'No model loaded' }

  return (
    <div className="topbar">
      <span className="breadcrumb">
        {group} / <strong>{title}</strong>
      </span>
      <span className="topbar-status">
        <span className="status-dot" data-tone={status.tone} aria-hidden="true" />
        {status.label}
        {modelLoaded && modelName && (
          <span className="model-name" title={modelName}>
            {modelName}
          </span>
        )}
      </span>
    </div>
  )
}

// Main app layout for regular windows
function MainLayout(): JSX.Element {
  const { fetchHealth, startRecording, setAppState } = useAppStore()
  const { upsertItem, fetchHistory } = useHistoryStore()
  const { fetchSettings, settings } = useSettingsStore()
  const { toast } = useToast()
  
  useEffect(() => {
    configureBackendPort().then(() => {
      fetchHealth()
      fetchHistory()
      fetchSettings()

      // Initialize WebSocket subscription for real-time transcription updates
      initHistoryWebSocket()
    })

    const interval = setInterval(fetchHealth, 5000)

    return () => clearInterval(interval)
  }, [fetchHealth, fetchHistory, fetchSettings])
  
  useHotkeyRegistration(settings?.hotkeys, (failed) => {
    const accelerators = failed.map((failure) => failure.accelerator).join(', ')
    toast.error(
      `Could not register hotkey${failed.length === 1 ? '' : 's'}: ${accelerators}`
    )
  })
   
  useEffect(() => {
    const unsubStart = window.api?.onRecordingStart(() => {
      startRecording()
    })
    
    const unsubComplete = window.api?.onRecordingComplete((result) => {
      setAppState('idle')
      const response = result as {
        id?: string
        text?: string
        duration_ms?: number
        model_used?: string | null
        language?: string | null
        original_text?: string | null
        processing_error?: string | null
      }
      if (response?.id && response?.text) {
        const originalText = response.original_text ?? null
        const record: TranscriptionRecord = {
          id: response.id,
          text: response.text,
          duration_ms: response.duration_ms ?? 0,
          model_used: response.model_used ?? null,
          language: response.language ?? null,
          created_at: new Date().toISOString(),
          original_text: originalText,
          is_ai_enhanced: originalText !== null && originalText !== response.text
        }
        upsertItem(record)
      }
      if (response?.processing_error) {
        toast.warning(
          `AI processing failed (${response.processing_error}). The fallback text was inserted.`
        )
      }
    })
    
    const unsubError = window.api?.onRecordingError((error) => {
      setAppState('idle')
      console.error('Recording error:', error)
    })
    
    return () => {
      unsubStart?.()
      unsubComplete?.()
      unsubError?.()
    }
  }, [startRecording, setAppState, upsertItem])
  
  return (
    <>
      <a
        className="skip-link"
        href="#content"
        onClick={(event) => {
          event.preventDefault()
          document.getElementById('content')?.focus()
        }}
      >
        Skip to content
      </a>
      <div className="shell">
        <Sidebar />

        <main className="main" id="content" tabIndex={-1}>
          <Topbar />
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/batch" element={<BatchTranscription />} />
              <Route path="/stats" element={<Stats />} />
              
              {/* Settings routes - redirect /settings to /settings/model */}
              <Route path="/settings" element={<Navigate to="/settings/model" replace />} />
              <Route path="/settings/model" element={<ModelSettings />} />
              <Route path="/settings/audio" element={<AudioSettings />} />
              <Route path="/settings/hotkey" element={<HotkeySettings />} />
              <Route path="/settings/processing" element={<ProcessingSettings />} />
              <Route path="/settings/behavior" element={<BehaviorSettings />} />
              <Route path="/settings/appearance" element={<AppearanceSettings />} />
              <Route path="/settings/data" element={<DataSettings />} />
              <Route path="/settings/about" element={<AboutSettings />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </>
  )
}

// App wrapper with router
function App(): JSX.Element {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <HashRouter>
          <NavigationListener />
          <ThemeInitializer />
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              {/* Recording indicator is a separate route for the overlay window */}
              <Route path="/recording-indicator" element={<RecordingIndicator />} />
              {/* All other routes use the main layout */}
              <Route path="/*" element={<MainLayout />} />
            </Routes>
          </Suspense>
        </HashRouter>
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App

// Type declarations for window.api
declare global {
  interface Window {
    api?: {
      showWindow: () => Promise<void>
      hideWindow: () => Promise<void>
      showIndicator: () => Promise<void>
      hideIndicator: () => Promise<void>
      resizeIndicator: (width: number, height: number) => Promise<void>
      setIgnoreMouseEvents: (ignore: boolean, options?: { forward: boolean }) => Promise<void>
      startRecording: () => Promise<void>
      stopRecording: () => Promise<void>
      cancelRecording: () => Promise<void>
      getRecordingStatus: () => Promise<boolean>
      getBackendStatus: () => Promise<{ running: boolean; port: number }>
      getBackendPort: () => Promise<number>
      checkHealth?: () => Promise<{ state: string }>
      registerHotkeys: (bindings: HotkeyBinding[]) => Promise<HotkeyRegistrationResult>
      getCurrentHotkeys: () => Promise<{ bindings: HotkeyBinding[] }>
      getVersion: () => Promise<string>
      quit: () => Promise<void>
      showError: (title: string, content: string) => Promise<void>
      showMessage: (options: MessageBoxOptions) => Promise<MessageBoxReturnValue>
      onNavigate: (callback: (path: string) => void) => () => void
      onRecordingStart: (callback: (payload: { mode: string | null }) => void) => () => void
      onRecordingLocked?: (callback: () => void) => () => void
      onRecordingProcessing: (callback: () => void) => () => void
      onRecordingComplete: (callback: (result: unknown) => void) => () => void
      onRecordingError: (callback: (error: string) => void) => () => void
      onLiveTranscript: (callback: (text: string) => void) => () => void
      sendLiveTranscript: (text: string) => Promise<void>
    }
  }
}
