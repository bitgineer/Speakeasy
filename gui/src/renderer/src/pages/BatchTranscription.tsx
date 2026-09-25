import { useState, useEffect, useCallback, type ChangeEvent, type DragEvent } from 'react'
import { Check, FileAudio, Loader2, Play, RotateCcw, Upload, X } from 'lucide-react'
import { apiClient } from '../api/client'
import wsClient from '../api/websocket'
import { Button } from '../components/ui/button'
import type {
  BatchFileStatus,
  BatchJob,
  BatchProgressEvent,
  WebSocketEvent
} from '../api/types'

const ACCEPTED_EXTENSIONS = /\.(mp3|wav|m4a|ogg|flac|mp4|mkv|mov|webm)$/i

const JOB_STATE: Record<
  BatchJob['status'],
  { heading: string; tone: 'accent' | 'success' | 'danger' }
> = {
  pending: { heading: 'Waiting to start', tone: 'accent' },
  processing: { heading: 'Processing batch...', tone: 'accent' },
  completed: { heading: 'Batch complete', tone: 'success' },
  failed: { heading: 'Batch failed', tone: 'danger' },
  cancelled: { heading: 'Batch cancelled', tone: 'danger' }
}

const FILE_TONE: Record<BatchFileStatus, 'accent' | 'success' | 'danger' | 'muted'> = {
  pending: 'muted',
  processing: 'accent',
  completed: 'success',
  failed: 'danger',
  skipped: 'muted'
}

function isAcceptedFile(file: File): boolean {
  return (
    file.type.startsWith('audio/') ||
    file.type.startsWith('video/') ||
    ACCEPTED_EXTENSIONS.test(file.name)
  )
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function fileGlyph(status: BatchFileStatus): JSX.Element {
  if (status === 'completed') return <Check size={15} strokeWidth={2.25} aria-hidden="true" />
  if (status === 'failed') return <X size={15} strokeWidth={2.25} aria-hidden="true" />
  if (status === 'processing') {
    return <Loader2 className="animate-spin" size={15} aria-hidden="true" />
  }
  return <span className="file-dot" aria-hidden="true" />
}

export default function BatchTranscription(): JSX.Element {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [job, setJob] = useState<BatchJob | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // WebSocket listener for progress updates
  useEffect(() => {
    const handleMessage = (event: WebSocketEvent) => {
      if (event.type === 'batch_progress') {
        const progressEvent = event as BatchProgressEvent
        // Only update if it matches our current job
        if (job && job.id === progressEvent.job_id) {
          setJob((prev) =>
            prev
              ? {
                  ...prev,
                  status: progressEvent.status,
                  current_file_index: progressEvent.current_index,
                  completed_count: progressEvent.completed,
                  failed_count: progressEvent.failed
                }
              : null
          )

          // A file status change means the file list is stale, so re-fetch it.
          if (progressEvent.file_status) {
            apiClient.getBatchJob(progressEvent.job_id).then(setJob).catch(console.error)
          }
        }
      }
    }

    const unsubscribe = wsClient.on('message', handleMessage)
    return () => {
      unsubscribe()
    }
  }, [job])

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).filter(isAcceptedFile)
      setSelectedFiles((prev) => [...prev, ...newFiles])
    }
  }, [])

  const handleFileSelect = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      setSelectedFiles((prev) => [...prev, ...newFiles])
    }
    // Reset input value to allow selecting the same file again if needed
    e.target.value = ''
  }, [])

  const removeFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const clearAll = useCallback(() => {
    setSelectedFiles([])
    setJob(null)
    setError(null)
  }, [])

  const startBatch = useCallback(async () => {
    if (selectedFiles.length === 0) return

    setIsLoading(true)
    setError(null)

    try {
      // Extract paths from File objects (Electron specific)
      const filePaths = selectedFiles.map((f) => (f as File & { path: string }).path)
      const response = await apiClient.createBatchJob({ file_paths: filePaths })
      const newJob = await apiClient.getBatchJob(response.job_id)
      setJob(newJob)
      setSelectedFiles([]) // Clear selection as they are now in the job
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to start the batch. Try again.')
    } finally {
      setIsLoading(false)
    }
  }, [selectedFiles])

  const retryFailed = useCallback(async () => {
    if (!job) return

    setIsLoading(true)
    try {
      const response = await apiClient.retryBatchJob(job.id)
      setJob(response.job)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to retry the batch. Try again.')
    } finally {
      setIsLoading(false)
    }
  }, [job])

  const progressPercent = job ? Math.round((job.completed_count / job.total_files) * 100) : 0

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Upload / transcribe</p>
          <h1>Batch transcription</h1>
          <p className="page-subtitle">Queue audio or video files and transcribe them in one run.</p>
        </div>
        {job && (
          <div className="page-actions">
            <Button variant="secondary" onClick={clearAll}>
              Start new batch
            </Button>
          </div>
        )}
      </header>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError(null)}
            title="Dismiss error"
            aria-label="Dismiss error"
          >
            <X size={14} aria-hidden="true" />
          </button>
        </div>
      )}

      {!job ? (
        <div className="batch-stack">
          <input
            type="file"
            id="file-input"
            multiple
            className="hidden"
            onChange={handleFileSelect}
            accept="audio/*,video/*"
          />

          <button
            type="button"
            className="dropzone"
            data-dragging={isDragging}
            onClick={() => document.getElementById('file-input')?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="dropzone-icon" size={28} strokeWidth={1.5} aria-hidden="true" />
            <span className="dropzone-title">Drop audio or video files here, or click to browse</span>
            <span className="dropzone-hint">MP3, WAV, M4A, MP4, MKV, and more</span>
          </button>

          {selectedFiles.length > 0 && (
            <section className="card queue" aria-label="Files ready to transcribe">
              <div className="queue-head">
                <span className="queue-title">
                  {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-danger-text"
                  onClick={() => setSelectedFiles([])}
                >
                  Clear all
                </Button>
              </div>
              <ul className="queue-list">
                {selectedFiles.map((file, index) => (
                  <li key={`${file.name}-${index}`} className="queue-item">
                    <span className="queue-file">
                      <span className="queue-glyph" aria-hidden="true">
                        <FileAudio size={15} strokeWidth={1.75} />
                      </span>
                      <span className="queue-meta">
                        <span className="queue-name" title={file.name}>
                          {file.name}
                        </span>
                        <span className="queue-size">{formatSize(file.size)}</span>
                      </span>
                    </span>
                    <button
                      type="button"
                      className="queue-remove"
                      onClick={() => removeFile(index)}
                      title={`Remove ${file.name}`}
                      aria-label={`Remove ${file.name}`}
                    >
                      <X size={15} aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
              <div className="queue-foot">
                <Button className="w-full" onClick={startBatch} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="animate-spin" size={15} aria-hidden="true" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play size={15} aria-hidden="true" />
                      Start batch transcription
                    </>
                  )}
                </Button>
              </div>
            </section>
          )}
        </div>
      ) : (
        <div className="batch-stack">
          <section className="card progress-panel">
            <div className="progress-head">
              <div>
                <h2 className="progress-title">{JOB_STATE[job.status].heading}</h2>
                <p className="progress-sub">
                  {job.status === 'processing'
                    ? `Processing file ${job.current_file_index + 1} of ${job.total_files}`
                    : `Processed ${job.completed_count} of ${job.total_files} files`}
                </p>
              </div>
              <span className="progress-pct">{progressPercent}%</span>
            </div>

            <div
              className="progress-track"
              role="progressbar"
              aria-valuenow={progressPercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Batch progress"
            >
              <div
                className="progress-fill"
                data-tone={JOB_STATE[job.status].tone}
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            <div className="progress-stats">
              <div>
                <div className="progress-stat-value" data-tone="success">
                  {job.completed_count}
                </div>
                <div className="progress-stat-label">Completed</div>
              </div>
              <div>
                <div className="progress-stat-value" data-tone="danger">
                  {job.failed_count}
                </div>
                <div className="progress-stat-label">Failed</div>
              </div>
              <div>
                <div className="progress-stat-value" data-tone="muted">
                  {job.skipped_count}
                </div>
                <div className="progress-stat-label">Skipped</div>
              </div>
            </div>
          </section>

          <section className="card files-panel" aria-label="Batch files">
            <div className="panel-head">
              <h2>Files</h2>
              <span className="muted">{job.files.length} total</span>
            </div>
            <ul className="file-list">
              {job.files.map((file) => {
                const tone = FILE_TONE[file.status]
                return (
                  <li key={file.id} className="file-row" data-status={file.status}>
                    <span className="file-main">
                      <span className="file-glyph" data-tone={tone} aria-hidden="true">
                        {fileGlyph(file.status)}
                      </span>
                      <span className="file-text">
                        <span className="file-name" title={file.filename}>
                          {file.filename}
                        </span>
                        {file.error && (
                          <span className="file-error" title={file.error}>
                            {file.error}
                          </span>
                        )}
                      </span>
                    </span>
                    <span className="pill capitalize" data-tone={tone}>
                      {file.status}
                    </span>
                  </li>
                )
              })}
            </ul>
            {job.failed_count > 0 && (
              <div className="files-foot">
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={retryFailed}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="animate-spin" size={15} aria-hidden="true" />
                      Retrying...
                    </>
                  ) : (
                    <>
                      <RotateCcw size={15} aria-hidden="true" />
                      Retry failed files
                    </>
                  )}
                </Button>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
