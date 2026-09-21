import { create } from 'zustand'
import { apiClient } from '../api/client'
import type { DownloadStatus, CachedModel, DownloadProgressEvent } from '../api/types'

interface DownloadStore {
  isDownloading: boolean
  downloadProgress: number
  downloadedBytes: number
  totalBytes: number
  modelName: string | null
  modelType: string | null
  status: DownloadStatus | null
  errorMessage: string | null
  elapsedSeconds: number
  bytesPerSecond: number
  estimatedRemainingSeconds: number | null
  
  cachedModels: CachedModel[]
  cacheDir: string | null
  totalCacheSize: number
  totalCacheSizeHuman: string | null
  
  isLoadingCache: boolean
  isClearingCache: boolean
  
  updateFromWebSocket: (event: DownloadProgressEvent) => void
  cancelDownload: () => Promise<boolean>
  fetchCachedModels: () => Promise<void>
  fetchCacheInfo: () => Promise<void>
  clearCache: (modelName?: string) => Promise<boolean>
  reset: () => void
}

const initialState = {
  isDownloading: false,
  downloadProgress: 0,
  downloadedBytes: 0,
  totalBytes: 0,
  modelName: null,
  modelType: null,
  status: null,
  errorMessage: null,
  elapsedSeconds: 0,
  bytesPerSecond: 0,
  estimatedRemainingSeconds: null,
  
  cachedModels: [],
  cacheDir: null,
  totalCacheSize: 0,
  totalCacheSizeHuman: null,
  
  isLoadingCache: false,
  isClearingCache: false,
}

export const useDownloadStore = create<DownloadStore>((set, get) => ({
  ...initialState,
  
  updateFromWebSocket: (event: DownloadProgressEvent) => {
    const isActive = event.status === 'pending' || event.status === 'downloading'
    
    set({
      isDownloading: isActive,
      downloadProgress: event.progress_percent,
      downloadedBytes: event.downloaded_bytes,
      totalBytes: event.total_bytes,
      modelName: event.model_name,
      modelType: event.model_type,
      status: event.status,
      errorMessage: event.error_message,
      elapsedSeconds: event.elapsed_seconds,
      bytesPerSecond: event.bytes_per_second,
      estimatedRemainingSeconds: event.estimated_remaining_seconds,
    })
    
    if (event.status === 'completed') {
      get().fetchCachedModels()
    }
  },
  
  cancelDownload: async () => {
    try {
      await apiClient.cancelDownload()
      set({ status: 'cancelled', isDownloading: false })
      return true
    } catch (error) {
      console.error('Failed to cancel download:', error)
      return false
    }
  },
  
  fetchCachedModels: async () => {
    set({ isLoadingCache: true })
    try {
      const response = await apiClient.getDownloadedModels()
      set({ 
        cachedModels: response.models,
        isLoadingCache: false 
      })
    } catch (error) {
      console.error('Failed to fetch cached models:', error)
      set({ isLoadingCache: false })
    }
  },
  
  fetchCacheInfo: async () => {
    set({ isLoadingCache: true })
    try {
      const response = await apiClient.getCacheInfo()
      set({
        cachedModels: response.models,
        cacheDir: response.cache_dir,
        totalCacheSize: response.total_size_bytes,
        totalCacheSizeHuman: response.total_size_human,
        isLoadingCache: false,
      })
    } catch (error) {
      console.error('Failed to fetch cache info:', error)
      set({ isLoadingCache: false })
    }
  },
  
  clearCache: async (modelName?: string) => {
    set({ isClearingCache: true })
    try {
      await apiClient.clearCache(modelName)
      await get().fetchCacheInfo()
      set({ isClearingCache: false })
      return true
    } catch (error) {
      console.error('Failed to clear cache:', error)
      set({ isClearingCache: false })
      return false
    }
  },
  
  reset: () => set(initialState),
}))

export default useDownloadStore
