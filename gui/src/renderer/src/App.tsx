/**
 * App Root Component
 * 
 * Sets up routing and global providers.
 * Uses HashRouter required for Electron file:// protocol.
 */

import { useEffect, lazy, Suspense } from 'react'
import { HashRouter, Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAppStore, useHistoryStore, useSettingsStore, initHistoryWebSocket } from './store'
import ErrorBoundary from './components/ErrorBoundary'
import LoadingSpinner from './components/LoadingSpinner'
import Sidebar from './components/Sidebar'
import { ToastProvider } from './context/ToastProvider'
import type { TranscriptionRecord } from './api/types'

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'))
const BatchTranscription = lazy(() => import('./pages/BatchTranscription'))
const Stats = lazy(() => import('./pages/Stats'))
const RecordingIndicator = lazy(() => import('./components/RecordingIndicator'))

// Settings pages
const ModelSettings = lazy(() => import('./pages/settings/ModelSettings'))
const AudioSettings = lazy(() => import('./pages/settings/AudioSettings'))
const HotkeySettings = lazy(() => import('./pages/settings/HotkeySettings'))
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

// Theme initializer - loads theme on startup
function ThemeInitializer(): null {
  const { settings, fetchSettings } = useSettingsStore()
  
  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])
  
  useEffect(() => {
    if (settings?.theme) {
      document.documentElement.setAttribute('data-theme', settings.theme)
    }
  }, [settings?.theme])
  
  return null
}

// Main app layout for regular windows
function MainLayout(): JSX.Element {
  const { backendConnected, fetchHealth, startRecording, setAppState, isReconnecting } = useAppStore()
  const { addItem, fetchHistory } = useHistoryStore()
  const { fetchSettings, settings } = useSettingsStore()
  
  useEffect(() => {
    fetchHealth()
    fetchHistory()
    fetchSettings()
    
    // Initialize WebSocket subscription for real-time transcription updates
    initHistoryWebSocket()
    
    const interval = setInterval(fetchHealth, 5000)
    
    return () => clearInterval(interval)
  }, [fetchHealth, fetchHistory, fetchSettings])
  
  useEffect(() => {
    if (settings?.hotkey && window.api) {
      window.api.registerHotkey(settings.hotkey, settings.hotkey_mode || 'toggle')
    }
  }, [settings?.hotkey, settings?.hotkey_mode])
   
  useEffect(() => {
    const unsubStart = window.api?.onRecordingStart(() => {
      startRecording()
    })
    
    const unsubComplete = window.api?.onRecordingComplete((result) => {
      setAppState('idle')
      const response = result as { id?: string; text?: string; duration_ms?: number; model_used?: string | null; language?: string | null }
      if (response?.id && response?.text) {
        const record: TranscriptionRecord = {
          id: response.id,
          text: response.text,
          duration_ms: response.duration_ms ?? 0,
          model_used: response.model_used ?? null,
          language: response.language ?? null,
          created_at: new Date().toISOString()
        }
        addItem(record)
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
  }, [startRecording, setAppState, addItem])
  
  return (
    <div className="h-screen flex bg-[var(--color-bg-primary)]">
      {/* Sidebar Navigation */}
      <Sidebar />
      
      {/* Main content */}
      <main className="flex-1 min-h-0 overflow-auto">
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
            <Route path="/settings/behavior" element={<BehaviorSettings />} />
            <Route path="/settings/appearance" element={<AppearanceSettings />} />
            <Route path="/settings/data" element={<DataSettings />} />
            <Route path="/settings/about" element={<AboutSettings />} />
          </Routes>
        </Suspense>
      </main>
    </div>
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
      getBackendStatus: () => Promise<{ running: boolean; port: number }>
      getBackendPort: () => Promise<number>
      registerHotkey: (hotkey: string, mode?: string) => Promise<boolean>
      unregisterHotkey: () => Promise<void>
      getCurrentHotkey: () => Promise<string | null>
      getVersion: () => Promise<string>
      quit: () => Promise<void>
      showError: (title: string, content: string) => Promise<void>
      showMessage: (options: Electron.MessageBoxOptions) => Promise<Electron.MessageBoxReturnValue>
      onNavigate: (callback: (path: string) => void) => () => void
      onRecordingStart: (callback: () => void) => () => void
      onRecordingProcessing: (callback: () => void) => () => void
      onRecordingComplete: (callback: (result: unknown) => void) => () => void
      onRecordingError: (callback: (error: string) => void) => () => void
    }
  }
}
