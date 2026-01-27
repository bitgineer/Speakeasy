/**
 * App Root Component
 * 
 * Sets up routing and global providers.
 * Uses HashRouter required for Electron file:// protocol.
 */

import { useEffect, lazy, Suspense } from 'react'
import { HashRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { useAppStore, useHistoryStore, useSettingsStore } from './store'
import ErrorBoundary from './components/ErrorBoundary'
import LoadingSpinner from './components/LoadingSpinner'
import { ToastProvider } from './context/ToastProvider'
import type { TranscriptionRecord } from './api/types'

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Settings = lazy(() => import('./pages/Settings'))
const BatchTranscription = lazy(() => import('./pages/BatchTranscription'))
const RecordingIndicator = lazy(() => import('./components/RecordingIndicator'))

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

// Main app layout for regular windows
function MainLayout(): JSX.Element {
  const { backendConnected, fetchHealth, startRecording, stopRecording, setAppState, isReconnecting } = useAppStore()
  const { addItem, fetchHistory } = useHistoryStore()
  const { fetchSettings, settings } = useSettingsStore()
  
  useEffect(() => {
    fetchHealth()
    fetchHistory()
    fetchSettings()
    
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
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-white">SpeakEasy</h1>
        <div className="flex items-center gap-3">
          {/* Connection status indicator */}
          <div className="flex items-center gap-2" title={backendConnected ? "Connected" : undefined}>
            <div 
              className={`rounded-full transition-all duration-300 ${
                backendConnected 
                  ? 'w-2 h-2 bg-green-500' 
                  : isReconnecting
                    ? 'w-3 h-3 bg-yellow-500 animate-pulse'
                    : 'w-3 h-3 bg-red-500'
              }`} 
            />
            {!backendConnected && (
              <span className="text-xs text-gray-400">
                {isReconnecting ? 'Reconnecting...' : 'Disconnected'}
              </span>
            )}
          </div>
          {/* Batch button */}
          <a 
            href="#/batch" 
            className="text-gray-400 hover:text-white transition-colors p-2"
            title="Batch Transcription"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </a>
          {/* Settings button */}
          <a 
            href="#/settings" 
            className="text-gray-400 hover:text-white transition-colors p-2"
            title="Settings"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </a>
        </div>
      </header>
      
      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/batch" element={<BatchTranscription />} />
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
      getBackendStatus: () => Promise<{ running: boolean; port: number }>
      getBackendPort: () => Promise<number>
      registerHotkey: (hotkey: string) => Promise<boolean>
      unregisterHotkey: () => Promise<void>
      getCurrentHotkey: () => Promise<string | null>
      getVersion: () => Promise<string>
      quit: () => Promise<void>
      showError: (title: string, content: string) => Promise<void>
      showMessage: (options: Electron.MessageBoxOptions) => Promise<Electron.MessageBoxReturnValue>
      onNavigate: (callback: (path: string) => void) => () => void
      onRecordingStart: (callback: () => void) => () => void
      onRecordingComplete: (callback: (result: unknown) => void) => () => void
      onRecordingError: (callback: (error: string) => void) => () => void
    }
  }
}
