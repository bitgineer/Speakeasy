/**
 * API Type Definitions
 *
 * Shapes the backend owns are aliased from the generated OpenAPI schema.
 * Regenerate with `npm run gen:api`.
 */

import type { components } from './generated'

type Schemas = components['schemas']

// Generated backend models

export type HealthResponse = Schemas['HealthResponse']

export type TranscribeStartResponse = Schemas['TranscribeStartResponse']
export type TranscribeStopRequest = Schemas['TranscribeStopRequest']
export type TranscribeStopResponse = Schemas['TranscribeStopResponse']

export type TranscriptionRecord = Schemas['TranscriptionRecord']

export type Settings = Schemas['AppSettings']
export type SettingsUpdateRequest = Schemas['SettingsUpdateRequest']
export type SettingsUpdateResponse = Schemas['SettingsUpdateResponse']

export type HotkeyBinding = Schemas['HotkeyBinding']
export type ProcessingMode = Schemas['ProcessingMode']
export type ProviderKind = Schemas['ProviderKind']
export type LlmProvider = Schemas['LlmProvider']
export type ToneProfile = Schemas['ToneProfile']
export type AppMatch = Schemas['AppMatch']
export type ModeStatusResponse = Schemas['ModeStatusResponse']
export type ProcessingStatusResponse = Schemas['ProcessingStatusResponse']
export type ProviderKeyResponse = Schemas['ProviderKeyResponse']
export type ProviderModel = Schemas['ProviderModelResponse']
export type ProviderModelsResponse = Schemas['ProviderModelsResponse']
export type FocusedAppResponse = Schemas['FocusedAppResponse']

/** `GET /api/settings/provider-keys` is a bare map in the schema, so it is typed here. */
export type ProviderKeysResponse = Record<string, boolean>

/** Result of the `hotkey:register` IPC call handled in the Electron main process. */
export interface HotkeyRegistrationFailure {
  accelerator: string
  error: string
}

export type HotkeyRegistrationResult =
  | { ok: true }
  | { ok: false; failed: HotkeyRegistrationFailure[] }

export type ModelLoadRequest = Schemas['ModelLoadRequest']

export type ExportFormat = Schemas['ExportFormat']
export type ExportRequest = Schemas['ExportRequest']

export type BatchCreateRequest = Schemas['BatchCreateRequest']
export type BatchRetryRequest = Schemas['BatchRetryRequest']

// WebSocket events: the schema models the payload, the wire message adds `type`.

export type WebSocketEventType =
  | 'connected'
  | 'status'
  | 'transcription'
  | 'transcription_progress'
  | 'download_progress'
  | 'batch_progress'
  | 'error'
  | 'live_transcript'

export interface WebSocketEvent {
  type: WebSocketEventType
  [key: string]: unknown
}

export type ConnectedEvent = Schemas['ConnectedEvent'] & { type: 'connected' }
export type StatusEvent = Schemas['StatusEvent'] & { type: 'status' }
export type TranscriptionEvent = Schemas['TranscriptionEvent'] & { type: 'transcription' }
export type TranscriptionProgressEvent = Schemas['TranscriptionProgressEvent'] & { type: 'transcription_progress' }
export type LiveTranscriptEvent = Schemas['LiveTranscriptEvent'] & { type: 'live_transcript' }
export type ErrorEvent = Schemas['ErrorEvent'] & { type: 'error' }
export type DownloadProgressEvent = Schemas['DownloadProgressEvent'] & { type: 'download_progress' }
export type BatchProgressEvent = Schemas['BatchProgressEvent'] & { type: 'batch_progress' }

export type DownloadStatus = DownloadProgressEvent['status']
export type BatchJobStatus = BatchProgressEvent['status']
export type BatchFileStatus = NonNullable<BatchProgressEvent['file_status']>

// Not modeled by a backend response model yet; typed by hand so the client stays strict.

export interface WordData {
  word: string
  probability: number
}

// The list endpoint supports field projection, so items stay loose in the schema; the record shape is pinned here.
export interface HistoryListResponse {
  items: TranscriptionRecord[]
  total: number
  next_cursor: string | null
}

export interface HistoryStats {
  total_count: number
  total_duration_ms: number
  first_transcription: string | null
  last_transcription: string | null
  today_count: number
  this_week_count: number
  this_month_count: number
}

export interface ModelInfo {
  name: string
  description: string
  models: Record<string, {
    vram_gb: number
    speed: string
    accuracy: string
  }>
  languages: string[]
}

export interface ModelsResponse {
  models: Record<string, ModelInfo>
  current: {
    type: string
    name: string
  } | null
}

export interface ModelRecommendation {
  recommendation: {
    model_type: string
    model_name: string
  }
  gpu: {
    available: boolean
    name: string | null
    vram_gb: number | null
  }
  reason: string
}

export interface AudioDevice {
  id: number
  name: string
  channels: number
  sample_rate: number
  is_default: boolean
}

export interface DevicesResponse {
  devices: AudioDevice[]
  current: string | null
}

export interface DownloadStatusResponse {
  download: DownloadProgressEvent | null
}

export interface CachedModel {
  model_name: string
  path: string
  size_bytes: number
  size_human: string
  source: string
}

export interface DownloadedModelsResponse {
  models: CachedModel[]
  count: number
}

export interface CacheInfoResponse {
  cache_dir: string
  total_models: number
  total_size_bytes: number
  total_size_human: string
  models: CachedModel[]
}

export interface CacheClearResponse {
  status: string
  cleared: string[]
  freed_bytes: number
  freed_human: string
}

export interface ImportRequest {
  data: {
    transcriptions: TranscriptionRecord[]
    [key: string]: unknown
  }
  merge?: boolean
}

export interface ImportResponse {
  status: string
  imported: number
  skipped: number
}

export interface BatchFile {
  id: string
  job_id: string
  filename: string
  file_path: string
  status: BatchFileStatus
  error: string | null
  transcription_id: string | null
}

export interface BatchJob {
  id: string
  status: BatchJobStatus
  files: BatchFile[]
  created_at: string
  completed_at: string | null
  current_file_index: number
  total_files: number
  completed_count: number
  failed_count: number
  skipped_count: number
}

export interface BatchCreateResponse {
  job_id: string
  status: string
  total_files: number
}

export interface BatchListResponse {
  jobs: BatchJob[]
}
