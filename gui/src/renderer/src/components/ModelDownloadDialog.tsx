import React, { useEffect } from 'react'
import useDownloadStore from '../store/download-store'

interface ModelDownloadDialogProps {
  isOpen: boolean
  onClose: () => void
  onRetry?: () => void
}

const formatBytes = (bytes: number, decimals = 2) => {
  if (!+bytes) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

const formatTime = (seconds: number | null) => {
  if (seconds === null || !isFinite(seconds)) return 'Calculating...'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

const ModelDownloadDialog: React.FC<ModelDownloadDialogProps> = ({
  isOpen,
  onClose,
  onRetry,
}) => {
  const {
    isDownloading,
    downloadProgress,
    downloadedBytes,
    totalBytes,
    modelName,
    status,
    errorMessage,
    bytesPerSecond,
    estimatedRemainingSeconds,
    cancelDownload,
  } = useDownloadStore()

  // Prevent scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  const isCompleted = status === 'completed'
  const isError = status === 'error'
  const isCancelled = status === 'cancelled'

  const handleCancel = async () => {
    await cancelDownload()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-labelledby="download-dialog-title"
    >
      <div className="w-full max-w-md transform overflow-hidden rounded-2xl bg-gray-800 border border-gray-700 p-6 text-left align-middle shadow-xl transition-all">
        
        {/* Header */}
        <h3
          id="download-dialog-title"
          className="text-lg font-medium leading-6 text-white mb-4 flex items-center gap-2"
        >
          {isCompleted ? (
            <>
              <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Download Complete
            </>
          ) : isError ? (
            <>
              <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Download Failed
            </>
          ) : isCancelled ? (
            <>
              <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Download Cancelled
            </>
          ) : (
            <>
              <svg className="w-6 h-6 text-blue-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Downloading Model
            </>
          )}
        </h3>

        {/* Content */}
        <div className="mt-2">
          <p className="text-sm text-gray-300 mb-4">
            {modelName ? `Model: ${modelName}` : 'Preparing download...'}
          </p>

          {isError && (
            <div className="bg-red-900/20 border border-red-900/50 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-400">
                {errorMessage || 'An unknown error occurred during download.'}
              </p>
            </div>
          )}

          {/* Progress Bar */}
          {!isCompleted && !isError && !isCancelled && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-gray-400">
                <span>{formatBytes(downloadedBytes)} / {formatBytes(totalBytes)}</span>
                <span>{Math.round(downloadProgress)}%</span>
              </div>
              <div className="h-2 w-full bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-300 ease-out"
                  style={{ width: `${downloadProgress}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>{formatBytes(bytesPerSecond)}/s</span>
                <span>ETA: {formatTime(estimatedRemainingSeconds)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end gap-3">
          {isDownloading ? (
            <button
              type="button"
              className="inline-flex justify-center rounded-lg border border-transparent bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 transition-colors"
              onClick={handleCancel}
            >
              Cancel Download
            </button>
          ) : (
            <>
              {(isError || isCancelled) && onRetry && (
                <button
                  type="button"
                  className="inline-flex justify-center rounded-lg border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors"
                  onClick={onRetry}
                >
                  Retry
                </button>
              )}
              <button
                type="button"
                className="inline-flex justify-center rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-sm font-medium text-white hover:bg-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2 transition-colors"
                onClick={onClose}
              >
                {isCompleted ? 'Done' : 'Close'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ModelDownloadDialog
