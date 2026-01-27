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
    <div className="h-full flex flex-col bg-gray-900 text-white p-6 overflow-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Batch Transcription</h1>
        {job && (
          <button 
            onClick={clearAll}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Start New Batch
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
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
                ? 'border-blue-500 bg-blue-500/10' 
                : 'border-gray-700 hover:border-gray-500 bg-gray-800/50'
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
              <svg className="w-12 h-12 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-lg font-medium text-gray-300">
                Drop audio files here or click to browse
              </p>
              <p className="text-sm text-gray-500">
                Supports MP3, WAV, M4A, MP4, MKV, and more
              </p>
            </div>
          </div>

          {selectedFiles.length > 0 && (
            <div className="flex-1 flex flex-col bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
              <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800/80">
                <span className="font-medium text-gray-300">{selectedFiles.length} files selected</span>
                <button 
                  onClick={() => setSelectedFiles([])}
                  className="text-sm text-red-400 hover:text-red-300"
                >
                  Clear All
                </button>
              </div>
              <div className="flex-1 overflow-auto p-2 space-y-2">
                {selectedFiles.map((file, index) => (
                  <div key={`${file.name}-${index}`} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg group">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-8 h-8 rounded bg-gray-600 flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                        </svg>
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-200 truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatSize(file.size)}</p>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                      className="p-1 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
              <div className="p-4 border-t border-gray-700 bg-gray-800/80">
                <button
                  onClick={startBatch}
                  disabled={isLoading}
                  className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex justify-between items-end mb-4">
              <div>
                <h2 className="text-lg font-semibold text-white mb-1">
                  {job.status === 'completed' ? 'Batch Complete' : 
                   job.status === 'failed' ? 'Batch Failed' : 
                   'Processing Batch...'}
                </h2>
                <p className="text-sm text-gray-400">
                  {job.status === 'processing' 
                    ? `Processing file ${job.current_file_index + 1} of ${job.total_files}`
                    : `Processed ${job.completed_count} of ${job.total_files} files`
                  }
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-400">
                  {Math.round((job.completed_count / job.total_files) * 100)}%
                </div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${
                  job.status === 'failed' ? 'bg-red-500' : 
                  job.status === 'completed' ? 'bg-green-500' : 
                  'bg-blue-500'
                }`}
                style={{ width: `${(job.completed_count / job.total_files) * 100}%` }}
              />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-700">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{job.completed_count}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">{job.failed_count}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-400">{job.skipped_count}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">Skipped</div>
              </div>
            </div>
          </div>

          {/* File List */}
          <div className="flex-1 bg-gray-800 rounded-xl overflow-hidden border border-gray-700 flex flex-col">
            <div className="p-4 border-b border-gray-700 font-medium text-gray-300">
              Files
            </div>
            <div className="flex-1 overflow-auto p-2 space-y-2">
              {job.files.map((file) => (
                <div 
                  key={file.id} 
                  className={`
                    flex items-center justify-between p-3 rounded-lg border
                    ${file.status === 'processing' ? 'bg-blue-900/20 border-blue-500/30' : 
                      file.status === 'completed' ? 'bg-green-900/10 border-green-500/20' :
                      file.status === 'failed' ? 'bg-red-900/10 border-red-500/20' :
                      'bg-gray-700/30 border-transparent'
                    }
                  `}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`
                      w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
                      ${file.status === 'completed' ? 'text-green-400' :
                        file.status === 'failed' ? 'text-red-400' :
                        file.status === 'processing' ? 'text-blue-400' :
                        'text-gray-500'
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
                      <p className="text-sm font-medium text-gray-200 truncate">{file.filename}</p>
                      {file.error && (
                        <p className="text-xs text-red-400 truncate">{file.error}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-xs font-medium px-2 py-1 rounded bg-gray-800 text-gray-400 capitalize">
                    {file.status}
                  </div>
                </div>
              ))}
            </div>
            
            {job.failed_count > 0 && (
              <div className="p-4 border-t border-gray-700 bg-gray-800/80">
                <button
                  onClick={retryFailed}
                  disabled={isLoading}
                  className="w-full py-2 px-4 bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
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
