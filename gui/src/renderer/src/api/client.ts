/**
 * Backend API Client
 * 
 * HTTP client for the FastAPI backend.
 */

import type {
  HealthResponse,
  TranscribeStartResponse,
  TranscribeStopRequest,
  TranscribeStopResponse,
  HistoryListResponse,
  TranscriptionRecord,
  HistoryStats,
  Settings,
  SettingsUpdateRequest,
  SettingsUpdateResponse,
  ModelsResponse,
  ModelLoadRequest,
  ModelRecommendation,
  DevicesResponse,
  DownloadStatusResponse,
  DownloadedModelsResponse,
  CacheInfoResponse,
  CacheClearResponse,
  ExportFormat,
  ExportRequest,
  ImportRequest,
  ImportResponse,
  BatchCreateRequest,
  BatchCreateResponse,
  BatchJob,
  BatchListResponse
} from './types'
import { createCache } from './cache'
import { perfMonitor } from '../utils/performance'

const DEFAULT_PORT = 8765
const BASE_URL = `http://127.0.0.1:${DEFAULT_PORT}`

class ApiClient {
  private baseUrl: string
  private cache = createCache()

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl
  }

  setPort(port: number): void {
    this.baseUrl = `http://127.0.0.1:${port}`
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`API Error (${response.status}): ${error}`)
    }

    return response.json()
  }

  private async cachedRequest<T>(
    endpoint: string,
    ttl: number
  ): Promise<T> {
    const cached = this.cache.get<T>(endpoint)
    if (cached !== undefined) {
      return cached
    }

    const data = await this.request<T>(endpoint)
    this.cache.set(endpoint, data, ttl)
    return data
  }

  // Health
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health')
  }

  // Transcription
  async startTranscription(): Promise<TranscribeStartResponse> {
    return this.request<TranscribeStartResponse>('/api/transcribe/start', {
      method: 'POST'
    })
  }

  async stopTranscription(
    options: TranscribeStopRequest = {}
  ): Promise<TranscribeStopResponse> {
    return this.request<TranscribeStopResponse>('/api/transcribe/stop', {
      method: 'POST',
      body: JSON.stringify(options)
    })
  }

  async cancelTranscription(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/api/transcribe/cancel', {
      method: 'POST'
    })
  }

   // History
   async getHistory(params?: {
     limit?: number
     offset?: number
     search?: string
   }): Promise<HistoryListResponse> {
     const searchParams = new URLSearchParams()
     if (params?.limit) searchParams.set('limit', String(params.limit))
     if (params?.offset) searchParams.set('offset', String(params.offset))
     if (params?.search) searchParams.set('search', params.search)
     
     const query = searchParams.toString()
     perfMonitor.markStart('api-get-history')
     try {
       return await this.request<HistoryListResponse>(
         `/api/history${query ? `?${query}` : ''}`
       )
     } finally {
       perfMonitor.markEnd('api-get-history')
     }
   }

  async getHistoryItem(id: string): Promise<TranscriptionRecord> {
    return this.request<TranscriptionRecord>(`/api/history/${id}`)
  }

  async deleteHistoryItem(id: string): Promise<{ deleted: boolean }> {
    return this.request<{ deleted: boolean }>(`/api/history/${id}`, {
      method: 'DELETE'
    })
  }

  async getHistoryStats(): Promise<HistoryStats> {
    return this.request<HistoryStats>('/api/history/stats')
  }

  // Settings
  async getSettings(): Promise<Settings> {
    return this.cachedRequest<Settings>('/api/settings', 1 * 60 * 1000)
  }

  async updateSettings(
    settings: SettingsUpdateRequest
  ): Promise<SettingsUpdateResponse> {
    const result = await this.request<SettingsUpdateResponse>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings)
    })
    this.cache.invalidate('/api/settings')
    return result
  }

   // Models
   async getModels(): Promise<ModelsResponse> {
     perfMonitor.markStart('api-get-models')
     try {
       return await this.cachedRequest<ModelsResponse>('/api/models', 5 * 60 * 1000)
     } finally {
       perfMonitor.markEnd('api-get-models')
     }
   }

  async getModelsByType(type: string): Promise<{
    models: string[]
    languages: string[]
    compute_types: string[]
    info: unknown
  }> {
    return this.request(`/api/models/${type}`)
  }

   async loadModel(request: ModelLoadRequest): Promise<{ status: string; model: string }> {
     perfMonitor.markStart('api-load-model')
     try {
       const result = await this.request<{ status: string; model: string }>('/api/models/load', {
         method: 'POST',
         body: JSON.stringify(request)
       })
       this.cache.invalidate('/api/models*')
       return result
     } finally {
       perfMonitor.markEnd('api-load-model')
     }
   }

  async unloadModel(): Promise<{ status: string }> {
    const result = await this.request<{ status: string }>('/api/models/unload', {
      method: 'POST'
    })
    this.cache.invalidate('/api/models*')
    return result
  }

  async getModelRecommendation(
    needsTranslation: boolean = false
  ): Promise<ModelRecommendation> {
    return this.request<ModelRecommendation>(
      `/api/models/recommend?needs_translation=${needsTranslation}`
    )
  }

  async getDownloadStatus(): Promise<DownloadStatusResponse> {
    return this.request<DownloadStatusResponse>('/api/models/download/status')
  }

  async cancelDownload(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/api/models/download/cancel', {
      method: 'POST'
    })
  }

  async getDownloadedModels(): Promise<DownloadedModelsResponse> {
    return this.request<DownloadedModelsResponse>('/api/models/downloaded')
  }

  async getCacheInfo(): Promise<CacheInfoResponse> {
    return this.request<CacheInfoResponse>('/api/models/cache')
  }

  async clearCache(modelName?: string): Promise<CacheClearResponse> {
    const query = modelName ? `?model_name=${encodeURIComponent(modelName)}` : ''
    return this.request<CacheClearResponse>(`/api/models/cache${query}`, {
      method: 'DELETE'
    })
  }

  // Devices
  async getDevices(): Promise<DevicesResponse> {
    return this.cachedRequest<DevicesResponse>('/api/devices', 2 * 60 * 1000)
  }

  async setDevice(deviceName: string): Promise<{ status: string; device: string }> {
    const result = await this.request<{ status: string; device: string }>(
      `/api/devices/${encodeURIComponent(deviceName)}`,
      { method: 'PUT' }
    )
    this.cache.invalidate('/api/devices')
    return result
  }

  async exportHistory(
    format: ExportFormat = 'json',
    includeMetadata: boolean = true
  ): Promise<Blob> {
    const url = `${this.baseUrl}/api/history/export?format=${format}&include_metadata=${includeMetadata}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`)
    }
    return response.blob()
  }

  async exportHistoryFiltered(request: ExportRequest): Promise<Blob> {
    const url = `${this.baseUrl}/api/history/export`
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    })
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`)
    }
    return response.blob()
  }

  async importHistory(request: ImportRequest): Promise<ImportResponse> {
    return this.request<ImportResponse>('/api/history/import', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  async createBatchJob(request: BatchCreateRequest): Promise<BatchCreateResponse> {
    return this.request<BatchCreateResponse>('/api/transcribe/batch', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  async getBatchJobs(): Promise<BatchListResponse> {
    return this.request<BatchListResponse>('/api/transcribe/batch')
  }

  async getBatchJob(jobId: string): Promise<BatchJob> {
    return this.request<BatchJob>(`/api/transcribe/batch/${jobId}`)
  }

  async cancelBatchJob(jobId: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/api/transcribe/batch/${jobId}/cancel`, {
      method: 'POST'
    })
  }

  async retryBatchJob(
    jobId: string,
    fileIds?: string[]
  ): Promise<{ status: string; job: BatchJob }> {
    return this.request<{ status: string; job: BatchJob }>(
      `/api/transcribe/batch/${jobId}/retry`,
      {
        method: 'POST',
        body: JSON.stringify({ file_ids: fileIds })
      }
    )
  }

  async deleteBatchJob(jobId: string): Promise<{ deleted: boolean }> {
    return this.request<{ deleted: boolean }>(`/api/transcribe/batch/${jobId}`, {
      method: 'DELETE'
    })
  }
}

// Singleton instance
export const apiClient = new ApiClient()

export default apiClient
