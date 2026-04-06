/**
 * Backend API Client
 * 
 * HTTP client for the FastAPI backend with retry logic, timeouts, and cancellation.
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
const DEFAULT_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// Abort controller registry for request cancellation
const abortControllers = new Map<string, AbortController>()

class ApiClient {
  private baseUrl: string
  private cache = createCache()

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl
  }

  setPort(port: number): void {
    this.baseUrl = `http://127.0.0.1:${port}`
  }

  /**
   * Cancel an in-flight request by endpoint pattern
   */
  cancelRequest(pattern: string): void {
    for (const [endpoint, controller] of abortControllers) {
      if (endpoint.includes(pattern)) {
        controller.abort()
        abortControllers.delete(endpoint)
      }
    }
  }

  /**
   * Check if backend is reachable
   */
  async isBackendReachable(): Promise<boolean> {
    try {
      await this.getHealth()
      return true
    } catch {
      return false
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requestOptions: { 
      timeout?: number
      retries?: number
      retryDelay?: number
      signal?: AbortSignal
    } = {}
  ): Promise<T> {
    const {
      timeout = DEFAULT_TIMEOUT,
      retries = MAX_RETRIES,
      retryDelay = RETRY_DELAY,
      signal
    } = requestOptions

    const url = `${this.baseUrl}${endpoint}`
    let lastError: Error | null = null

    for (let attempt = 0; attempt <= retries; attempt++) {
      // Create abort controller for timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeout)

      // Register controller for cancellation support
      abortControllers.set(endpoint, controller)

      // Combine with external signal if provided
      if (signal) {
        signal.addEventListener('abort', () => controller.abort())
      }

      try {
        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          }
        })

        clearTimeout(timeoutId)
        abortControllers.delete(endpoint)

        if (!response.ok) {
          let errorData: unknown
          const contentType = response.headers.get('content-type')
          
          try {
            if (contentType?.includes('application/json')) {
              errorData = await response.json()
            } else {
              errorData = await response.text()
            }
          } catch {
            errorData = 'Unknown error'
          }

          const errorMessage = typeof errorData === 'object' && errorData !== null
            ? (errorData as { detail?: string }).detail || JSON.stringify(errorData)
            : String(errorData)

          throw new ApiError(
            `API Error (${response.status}): ${errorMessage}`,
            response.status,
            errorData
          )
        }

        return response.json()
      } catch (error) {
        clearTimeout(timeoutId)
        abortControllers.delete(endpoint)

        // Don't retry on user abort
        if (error instanceof Error && error.name === 'AbortError') {
          throw new ApiError('Request cancelled', undefined, { cancelled: true })
        }

        lastError = error instanceof Error ? error : new Error(String(error))

        // Don't retry client errors (4xx) except 429 (rate limit)
        if (error instanceof ApiError && error.status) {
          if (error.status >= 400 && error.status < 500 && error.status !== 429) {
            throw error
          }
        }

        // Retry with exponential backoff
        if (attempt < retries) {
          const delay = retryDelay * Math.pow(2, attempt)
          console.warn(`Request failed (${endpoint}), retrying in ${delay}ms (attempt ${attempt + 1}/${retries + 1}): ${lastError.message}`)
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }
    }

    throw lastError || new ApiError('Request failed after all retries')
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
    return this.cachedRequest<Settings>('/api/settings', 2 * 1000)
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

// Export types
export type { ApiClient }

export default apiClient
