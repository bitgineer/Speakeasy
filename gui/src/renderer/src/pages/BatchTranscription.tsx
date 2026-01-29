import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient } from '../api/client'
import wsClient from '../api/websocket'
import type { BatchJob, BatchProgressEvent, WebSocketEvent } from '../api/types'

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
          setJob(prev => prev ? {
            ...prev,
            status: progressEvent.status,
            current_file_index: progressEvent.current_index,
            completed_count: progressEvent.completed,
            failed_count: progressEvent.failed,
            // We might need to refresh the full job to get updated file statuses
            // but for the progress bar, the event data is enough
          } : null)
          
          // If a file status changed, we should probably re-fetch the job to get the updated file list
          // or we could try to patch it locally if the event gave us enough info
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

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).filter(file => 
        file.type.startsWith('audio/') || file.type.startsWith('video/') || 
        // Fallback for some formats that might not have mime type detected correctly
        /\.(mp3|wav|m4a|ogg|flac|mp4|mkv|mov|webm)$/i.test(file.name)
      )
      
      setSelectedFiles(prev => [...prev, ...newFiles])
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      setSelectedFiles(prev => [...prev, ...newFiles])
    }
    // Reset input value to allow selecting the same file again if needed
    e.target.value = ''
  }, [])

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
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
      const filePaths = selectedFiles.map(f => (f as any).path)
      
      const response = await apiClient.createBatchJob({
        file_paths: filePaths
      })
      
      const newJob = await apiClient.getBatchJob(response.job_id)
      setJob(newJob)
      setSelectedFiles([]) // Clear selection as they are now in the job
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start batch job')
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
      setError(err instanceof Error ? err.message : 'Failed to retry job')
    } finally {
      setIsLoading(false)
    }
  }, [job])

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="h-full flex flex-col bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] p-6 overflow-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Batch Transcription</h1>
        {job && (
          <button 
            onClick={clearAll}
            className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            Start New Batch
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg text-[var(--color-error)]">
          {error}
        </div>
      )}

      {!job ? (
        // File Selection State
        <div className="flex-1 flex flex-col gap-6">
          <div 
            className={`
              border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
              ${isDragging 
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)]' 
                : 'border-[var(--color-border)] hover:border-[var(--color-border-strong)] bg-[var(--color-bg-tertiary)]'
              }
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input 
              type="file" 
              id="file-input" 
              multiple 
              className="hidden" 
              onChange={handleFileSelect}
              accept="audio/*,video/*"
            />
            <div className="flex flex-col items-center gap-3">
              <svg className="w-12 h-12 text-[var(--color-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-lg font-medium text-[var(--color-text-secondary)]">
                Drop audio files here or click to browse
              </p>
              <p className="text-sm text-[var(--color-text-muted)]">
                Supports MP3, WAV, M4A, MP4, MKV, and more
              </p>
            </div>
          </div>

          {selectedFiles.length > 0 && (
            <div className="flex-1 flex flex-col bg-[var(--color-bg-secondary)] rounded-xl overflow-hidden border border-[var(--color-border)]">
              <div className="p-4 border-b border-[var(--color-border)] flex justify-between items-center bg-[var(--color-bg-tertiary)]">
                <span className="font-medium text-[var(--color-text-secondary)]">{selectedFiles.length} files selected</span>
                <button 
                  onClick={() => setSelectedFiles([])}
                  className="text-sm text-[var(--color-error)] hover:text-[var(--color-error-hover)]"
                >
                  Clear All
                </button>
              </div>
              <div className="flex-1 overflow-auto p-2 space-y-2">
                {selectedFiles.map((file, index) => (
                  <div key={`${file.name}-${index}`} className="flex items-center justify-between p-3 bg-[var(--color-bg-tertiary)] rounded-lg group">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-8 h-8 rounded bg-[var(--color-bg-elevated)] flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-[var(--color-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                        </svg>
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-[var(--color-text-secondary)] truncate">{file.name}</p>
                        <p className="text-xs text-[var(--color-text-muted)]">{formatSize(file.size)}</p>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                      className="p-1 text-[var(--color-text-muted)] hover:text-[var(--color-error)] opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
              <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-tertiary)]">
                <button
                  onClick={startBatch}
                  disabled={isLoading}
                  className="w-full py-3 px-4 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] disabled:opacity-50 disabled:cursor-not-allowed text-[var(--color-text-on-accent)] font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Start Batch Transcription
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        // Job Progress/Results State
        <div className="flex-1 flex flex-col gap-6">
          {/* Progress Header */}
          <div className="bg-[var(--color-bg-secondary)] rounded-xl p-6 border border-[var(--color-border)]">
            <div className="flex justify-between items-end mb-4">
              <div>
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-1">
                  {job.status === 'completed' ? 'Batch Complete' : 
                   job.status === 'failed' ? 'Batch Failed' : 
                   'Processing Batch...'}
                </h2>
                <p className="text-sm text-[var(--color-text-muted)]">
                  {job.status === 'processing' 
                    ? `Processing file ${job.current_file_index + 1} of ${job.total_files}`
                    : `Processed ${job.completed_count} of ${job.total_files} files`
                  }
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-[var(--color-accent)]">
                  {Math.round((job.completed_count / job.total_files) * 100)}%
                </div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="h-2 bg-[var(--color-bg-tertiary)] rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${
                  job.status === 'failed' ? 'bg-[var(--color-error)]' : 
                  job.status === 'completed' ? 'bg-[var(--color-success)]' : 
                  'bg-[var(--color-accent)]'
                }`}
                style={{ width: `${(job.completed_count / job.total_files) * 100}%` }}
              />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-[var(--color-border)]">
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--color-success)]">{job.completed_count}</div>
                <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--color-error)]">{job.failed_count}</div>
                <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--color-text-muted)]">{job.skipped_count}</div>
                <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">Skipped</div>
              </div>
            </div>
          </div>

          {/* File List */}
          <div className="flex-1 bg-[var(--color-bg-secondary)] rounded-xl overflow-hidden border border-[var(--color-border)] flex flex-col">
            <div className="p-4 border-b border-[var(--color-border)] font-medium text-[var(--color-text-secondary)]">
              Files
            </div>
            <div className="flex-1 overflow-auto p-2 space-y-2">
              {job.files.map((file) => (
                <div 
                  key={file.id} 
                  className={`
                    flex items-center justify-between p-3 rounded-lg border
                    ${file.status === 'processing' ? 'bg-[var(--color-info-muted)] border-[var(--color-info)]' : 
                      file.status === 'completed' ? 'bg-[var(--color-success-muted)] border-[var(--color-success)]' :
                      file.status === 'failed' ? 'bg-[var(--color-error-muted)] border-[var(--color-error)]' :
                      'bg-[var(--color-bg-tertiary)] border-transparent'
                    }
                  `}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`
                      w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
                      ${file.status === 'completed' ? 'text-[var(--color-success)]' :
                        file.status === 'failed' ? 'text-[var(--color-error)]' :
                        file.status === 'processing' ? 'text-[var(--color-info)]' :
                        'text-[var(--color-text-muted)]'
                      }
                    `}>
                      {file.status === 'completed' ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : file.status === 'failed' ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      ) : file.status === 'processing' ? (
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <div className="w-2 h-2 bg-current rounded-full" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[var(--color-text-secondary)] truncate">{file.filename}</p>
                      {file.error && (
                        <p className="text-xs text-[var(--color-error)] truncate">{file.error}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-xs font-medium px-2 py-1 rounded bg-[var(--color-bg-secondary)] text-[var(--color-text-muted)] capitalize">
                    {file.status}
                  </div>
                </div>
              ))}
            </div>
            
            {job.failed_count > 0 && (
              <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-tertiary)]">
                <button
                  onClick={retryFailed}
                  disabled={isLoading}
                  className="w-full py-2 px-4 bg-[var(--color-bg-elevated)] hover:bg-[var(--color-bg-secondary)] text-[var(--color-text-primary)] font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? 'Retrying...' : 'Retry Failed Files'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
