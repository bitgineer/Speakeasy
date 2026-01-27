/**
 * Settings Store - User preferences
 * 
 * Syncs settings with the backend and manages local state.
 */

import { create } from 'zustand'
import { apiClient } from '../api/client'
import type { Settings, SettingsUpdateRequest, ModelsResponse, DevicesResponse, AudioDevice, ModelInfo } from '../api/types'

interface SettingsStore {
  // Settings state
  settings: Settings | null
  isLoading: boolean
  isSaving: boolean
  error: string | null
  
  // Available options
  availableModels: Record<string, ModelInfo>
  availableDevices: AudioDevice[]
  currentDevice: string | null
  
  // Computed
  needsModelReload: boolean
  
  // Async operation states
  isLoadingModel: boolean
  isConnectingDevice: boolean
  hasUnsavedChanges: boolean
  originalSettings: Settings | null
  
  // Actions
  fetchSettings: () => Promise<void>
  updateSettings: (updates: SettingsUpdateRequest) => Promise<boolean>
  
  fetchModels: () => Promise<void>
  fetchDevices: () => Promise<void>
  
  loadModel: (modelType: string, modelName: string) => Promise<boolean>
  setDevice: (deviceName: string) => Promise<boolean>
  
  setError: (error: string | null) => void
  clearError: () => void
  
  setLoadingModel: (loading: boolean) => void
  setConnectingDevice: (connecting: boolean) => void
  setHasUnsavedChanges: (hasChanges: boolean) => void
  checkUnsavedChanges: (currentSettings: Settings) => boolean
}

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  // Initial state
  settings: null,
  isLoading: false,
  isSaving: false,
  error: null,
  
  availableModels: {},
  availableDevices: [],
  currentDevice: null,
  
  needsModelReload: false,
  
  isLoadingModel: false,
  isConnectingDevice: false,
  hasUnsavedChanges: false,
  originalSettings: null,
  
  // Actions
  fetchSettings: async () => {
    set({ isLoading: true, error: null })
    try {
      const settings = await apiClient.getSettings()
      set({ settings, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch settings',
        isLoading: false
      })
    }
  },
  
  updateSettings: async (updates) => {
    set({ isSaving: true, error: null })
    try {
      const response = await apiClient.updateSettings(updates)
      set({ 
        settings: response.settings,
        needsModelReload: response.reload_required,
        isSaving: false
      })
      return true
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to update settings',
        isSaving: false
      })
      return false
    }
  },
  
  fetchModels: async () => {
    try {
      const response: ModelsResponse = await apiClient.getModels()
      set({ availableModels: response.models })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch models'
      })
    }
  },
  
  fetchDevices: async () => {
    try {
      const response: DevicesResponse = await apiClient.getDevices()
      set({ 
        availableDevices: response.devices,
        currentDevice: response.current
      })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch devices'
      })
    }
  },
  
  loadModel: async (modelType, modelName) => {
    set({ isSaving: true, error: null })
    try {
      const { settings } = get()
      await apiClient.loadModel({
        model_type: modelType,
        model_name: modelName,
        device: settings?.device,
        compute_type: settings?.compute_type
      })
      set({ needsModelReload: false, isSaving: false })
      return true
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to load model',
        isSaving: false
      })
      return false
    }
  },
  
  setDevice: async (deviceName) => {
    try {
      await apiClient.setDevice(deviceName)
      set({ currentDevice: deviceName })
      
      // Also update settings
      const { settings } = get()
      if (settings) {
        set({ settings: { ...settings, device_name: deviceName } })
      }
      return true
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to set device'
      })
      return false
    }
  },
  
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  
  setLoadingModel: (loading) => set({ isLoadingModel: loading }),
  setConnectingDevice: (connecting) => set({ isConnectingDevice: connecting }),
  setHasUnsavedChanges: (hasChanges) => set({ hasUnsavedChanges: hasChanges }),
  checkUnsavedChanges: (currentSettings) => {
    const { originalSettings } = get()
    if (!originalSettings) return false
    return JSON.stringify(originalSettings) !== JSON.stringify(currentSettings)
  }
}))

export default useSettingsStore
