/**
 * API Type Definitions
 * 
 * Matches the backend FastAPI schemas.
 */

// Health response
export interface HealthResponse {
  status: string
  state: string
  model_loaded: boolean
  model_name: string | null
  gpu_available: boolean
  gpu_name: string | null
  gpu_vram_gb: number | null
}

// Transcription
export interface TranscribeStartResponse {
  status: string
}

export interface TranscribeStopRequest {
  auto_paste?: boolean
  language?: string | null
}

export interface TranscribeStopResponse {
  id: string
  text: string
  duration_ms: number
  model_used: string | null
  language: string | null
}

// History
export interface TranscriptionRecord {
  id: string
  text: string
  duration_ms: number
  model_used: string | null
  language: string | null
  created_at: string
}

export interface HistoryListResponse {
  items: TranscriptionRecord[]
  total: number
}

export interface HistoryStats {
  total_count: number
  total_duration_ms: number
  first_transcription: string | null
  last_transcription: string | null
}

// Settings
export interface Settings {
  model_type: string
  model_name: string
  compute_type: string
  device: string
  language: string
  device_name: string | null
  hotkey: string
  hotkey_mode: 'toggle' | 'push-to-talk'
  auto_paste: boolean
  show_recording_indicator: boolean
  always_show_indicator: boolean
  theme: string
  enable_text_cleanup: boolean
  custom_filler_words: string[] | null
  server_port: number
}

export interface SettingsUpdateRequest {
  model_type?: string
  model_name?: string
  compute_type?: string
  device?: string
  language?: string
  device_name?: string | null
  hotkey?: string
  hotkey_mode?: 'toggle' | 'push-to-talk'
  auto_paste?: boolean
  show_recording_indicator?: boolean
  always_show_indicator?: boolean
  theme?: string
  enable_text_cleanup?: boolean
  custom_filler_words?: string[] | null
}

export interface SettingsUpdateResponse {
  status: string
  settings: Settings
  reload_required: boolean
}

// Models
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

export interface ModelLoadRequest {
  model_type: string
  model_name: string
  device?: string
  compute_type?: string | null
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

// Audio Devices
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

// WebSocket Events
export type WebSocketEventType = 
  | 'connected'
  | 'status'
  | 'transcription'
  | 'download_progress'
  | 'batch_progress'
  | 'error'

export interface WebSocketEvent {
  type: WebSocketEventType
  [key: string]: unknown
}

export interface StatusEvent extends WebSocketEvent {
  type: 'status'
  state: string
  recording: boolean
}

export interface TranscriptionEvent extends WebSocketEvent {
  type: 'transcription'
  id: string
  text: string
  duration_ms: number
}

export interface ErrorEvent extends WebSocketEvent {
  type: 'error'
  message: string
}

// Download Progress Types
export type DownloadStatus = 'pending' | 'downloading' | 'completed' | 'cancelled' | 'error'

export interface DownloadProgressEvent extends WebSocketEvent {
  type: 'download_progress'
  download_id: string
  model_name: string
  model_type: string
  downloaded_bytes: number
  total_bytes: number
  progress_percent: number
  status: DownloadStatus
  error_message: string | null
  elapsed_seconds: number
  bytes_per_second: number
  estimated_remaining_seconds: number | null
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

// Export Types
export type ExportFormat = 'txt' | 'json' | 'csv' | 'srt' | 'vtt'

export interface ExportRequest {
  format: ExportFormat
  include_metadata?: boolean
  start_date?: string
  end_date?: string
  search?: string
  record_ids?: string[]
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

// Batch Transcription Types
export type BatchJobStatus = 'pending' | 'processing' | 'completed' | 'cancelled' | 'failed'
export type BatchFileStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'

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

export interface BatchCreateRequest {
  file_paths: string[]
}

export interface BatchCreateResponse {
  job_id: string
  status: string
  total_files: number
}

export interface BatchListResponse {
  jobs: BatchJob[]
}

export interface BatchProgressEvent extends WebSocketEvent {
  type: 'batch_progress'
  job_id: string
  status: BatchJobStatus
  current_file: string | null
  current_index: number
  total_files: number
  completed: number
  failed: number
  file_status?: BatchFileStatus
}
