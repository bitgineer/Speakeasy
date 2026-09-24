import React, { useEffect } from 'react'
import { AlertTriangle, CheckCircle2, Download, XCircle } from 'lucide-react'
import { Button } from './ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog'
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

  const heading = isCompleted
    ? {
        icon: <CheckCircle2 size={18} className="text-success-text" aria-hidden="true" />,
        title: 'Download complete'
      }
    : isError
      ? {
          icon: <XCircle size={18} className="text-danger-text" aria-hidden="true" />,
          title: 'Download failed'
        }
      : isCancelled
        ? {
            icon: <AlertTriangle size={18} className="text-warning-text" aria-hidden="true" />,
            title: 'Download cancelled'
          }
        : {
            icon: <Download size={18} className="animate-pulse text-accent-text" aria-hidden="true" />,
            title: 'Downloading model'
          }

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      {/* Radix warns without a Description; the dialog carries its title only. */}
      <DialogContent className="max-w-md" aria-describedby={undefined}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {heading.icon}
            {heading.title}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <p className="text-small text-content-secondary">
            {modelName ? `Model: ${modelName}` : 'Preparing download...'}
          </p>

          {isError && (
            <div
              className="rounded-control border border-danger-border bg-danger-muted p-3"
              role="alert"
            >
              <p className="text-small text-danger-text wrap-anywhere">
                {errorMessage || 'The download failed. Close this dialog and try again.'}
              </p>
            </div>
          )}

          {!isCompleted && !isError && !isCancelled && (
            <div className="space-y-2">
              <div className="flex justify-between text-caption text-content-muted">
                <span>{formatBytes(downloadedBytes)} / {formatBytes(totalBytes)}</span>
                <span>{Math.round(downloadProgress)}%</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  data-tone="accent"
                  style={{ width: `${downloadProgress}%` }}
                />
              </div>
              <div className="flex justify-between text-caption text-content-muted">
                <span>{formatBytes(bytesPerSecond)}/s</span>
                <span>ETA: {formatTime(estimatedRemainingSeconds)}</span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          {isDownloading ? (
            <Button
              type="button"
              variant="ghost"
              className="text-danger-text hover:bg-danger-muted hover:text-danger-text"
              onClick={handleCancel}
            >
              Cancel download
            </Button>
          ) : (
            <>
              {(isError || isCancelled) && onRetry && (
                <Button type="button" onClick={onRetry}>
                  Retry
                </Button>
              )}
              <Button type="button" variant="secondary" onClick={onClose}>
                {isCompleted ? 'Done' : 'Close'}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ModelDownloadDialog
