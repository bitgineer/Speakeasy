/**
 * App Store - Core application state
 * 
 * Manages recording state, backend connection, and model status.
 */

import { create } from 'zustand'
import { apiClient } from '../api/client'
import type { HealthResponse } from '../api/types'

export type AppState = 'idle' | 'recording' | 'transcribing' | 'error'

interface AppStore {
  // Connection state
  backendConnected: boolean
  wsConnected: boolean
  backendPort: number
  
  // Recording state
  appState: AppState
  isRecording: boolean
  recordingStartTime: number | null
  recordingDuration: number
  
  // Model state
  modelLoaded: boolean
  modelName: string | null
  modelType: string | null
  
  // GPU info
  gpuAvailable: boolean
  gpuName: string | null
  gpuVramGb: number | null
  
  // Error state
  lastError: string | null
  
  // Async operation states
  isTranscribing: boolean
  isSaving: boolean
  lastOperationStatus: { type: 'success' | 'error'; message: string } | null
  isReconnecting: boolean
  
  // Actions
  setBackendConnected: (connected: boolean) => void
  setWsConnected: (connected: boolean) => void
  setBackendPort: (port: number) => void
  
  setAppState: (state: AppState) => void
  startRecording: () => void
  stopRecording: () => void
  
  setModelInfo: (loaded: boolean, name: string | null, type: string | null) => void
  setGpuInfo: (available: boolean, name: string | null, vramGb: number | null) => void
  
  setError: (error: string | null) => void
  clearError: () => void
  
  setTranscribing: (isTranscribing: boolean) => void
  setSaving: (isSaving: boolean) => void
  setOperationStatus: (status: { type: 'success' | 'error'; message: string } | null) => void
  setReconnecting: (isReconnecting: boolean) => void
  
  // Sync with backend
  syncWithHealth: (health: HealthResponse) => void
  fetchHealth: () => Promise<void>
  
  // Recording timer
  updateRecordingDuration: () => void
}

export const useAppStore = create<AppStore>((set, get) => ({
  // Initial state
  backendConnected: false,
  wsConnected: false,
  backendPort: 8765,
  
  appState: 'idle',
  isRecording: false,
  recordingStartTime: null,
  recordingDuration: 0,
  
  modelLoaded: false,
  modelName: null,
  modelType: null,
  
  gpuAvailable: false,
  gpuName: null,
  gpuVramGb: null,
  
  lastError: null,
  
  isTranscribing: false,
  isSaving: false,
  lastOperationStatus: null,
  isReconnecting: false,
  
  // Actions
  setBackendConnected: (connected) => set({ backendConnected: connected }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setBackendPort: (port) => {
    apiClient.setPort(port)
    set({ backendPort: port })
  },
  
  setAppState: (state) => set({ 
    appState: state,
    isRecording: state === 'recording'
  }),
  
  startRecording: () => set({
    appState: 'recording',
    isRecording: true,
    recordingStartTime: Date.now(),
    recordingDuration: 0
  }),
  
  stopRecording: () => set({
    appState: 'transcribing',
    isRecording: false,
    recordingStartTime: null
  }),
  
  setModelInfo: (loaded, name, type) => set({
    modelLoaded: loaded,
    modelName: name,
    modelType: type
  }),
  
  setGpuInfo: (available, name, vramGb) => set({
    gpuAvailable: available,
    gpuName: name,
    gpuVramGb: vramGb
  }),
  
  setError: (error) => set({ 
    lastError: error,
    appState: error ? 'error' : get().appState
  }),
  
  clearError: () => set({ lastError: null }),
  
  setTranscribing: (isTranscribing) => set({ isTranscribing }),
  setSaving: (isSaving) => set({ isSaving }),
  setOperationStatus: (status) => set({ lastOperationStatus: status }),
  setReconnecting: (isReconnecting) => set({ isReconnecting }),
  
  syncWithHealth: (health) => {
    const state = health.state as AppState
    set({
      backendConnected: health.status === 'ok',
      appState: state,
      isRecording: state === 'recording',
      modelLoaded: health.model_loaded,
      modelName: health.model_name,
      gpuAvailable: health.gpu_available,
      gpuName: health.gpu_name,
      gpuVramGb: health.gpu_vram_gb
    })
  },
  
  fetchHealth: async () => {
    if (!get().backendConnected) {
      set({ isReconnecting: true })
    }
    try {
      const health = await apiClient.getHealth()
      get().syncWithHealth(health)
      set({ isReconnecting: false })
    } catch (error) {
      set({ 
        backendConnected: false,
        lastError: error instanceof Error ? error.message : 'Failed to connect to backend',
        isReconnecting: false
      })
    }
  },
  
  updateRecordingDuration: () => {
    const { recordingStartTime, isRecording } = get()
    if (isRecording && recordingStartTime) {
      set({ recordingDuration: Date.now() - recordingStartTime })
    }
  }
}))

export default useAppStore
