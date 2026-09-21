/**
 * HistoryItem Component
 * 
 * Displays a single transcription record with copy and delete actions.
 */

import { useState, memo, useEffect, useRef } from 'react'
import type { TranscriptionRecord } from '../api/types'
import ExportDialog from './ExportDialog'

interface HistoryItemProps {
  item: TranscriptionRecord
  onDelete: (id: string) => Promise<void>
  index?: number
}

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  
  // Reset time part for date comparison
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const recordDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  
  const diffTime = today.getTime() - recordDate.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    // Today - show time
    return date.toLocaleTimeString(undefined, { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7 && diffDays > 0) {
    return date.toLocaleDateString(undefined, { weekday: 'long' })
  } else {
    return date.toLocaleDateString(undefined, { 
      month: 'short', 
      day: 'numeric',
      year: diffDays > 365 ? 'numeric' : undefined
    })
  }
}

function HistoryItem({ item, onDelete, index }: HistoryItemProps): JSX.Element {
  const [copied, setCopied] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [showOriginal, setShowOriginal] = useState(false)
const [isFlashing, setIsFlashing] = useState(false)
const prevTextRef = useRef(item.text)

// Flash effect only for the newest transcription (first item) when text updates
useEffect(() => {
  // Only flash if this is the newest item (index 0) and text actually changed
  if (index === 0 && prevTextRef.current !== item.text) {
    setIsFlashing(true)
    const timer = setTimeout(() => setIsFlashing(false), 2000)
    prevTextRef.current = item.text
    return () => clearTimeout(timer)
  }
}, [item.text, index])
  
  // Get the text to display based on toggle state
  const displayText = showOriginal && item.original_text ? item.original_text : item.text
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(displayText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }
  
  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await onDelete(item.id)
    } finally {
      setIsDeleting(false)
      setShowDeleteConfirm(false)
    }
  }
  
  return (
    <div className={`
      group relative p-4 rounded-lg border border-[var(--color-border)]
      bg-[var(--color-bg-secondary)] transition-all duration-200 ease-out
      hover:border-[var(--color-border-strong)]
      hover:shadow-md hover:-translate-y-px cursor-pointer
      ${isFlashing ? 'ring-2 ring-yellow-500/50 bg-yellow-500/10 shadow-[0_0_20px_rgba(234,179,8,0.3)]' : ''}
    `}>
      {/* Header with metadata */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
          <span title={new Date(item.created_at).toLocaleString()}>
            {formatDate(item.created_at)}
          </span>
          <span className="text-[var(--color-border-strong)]">|</span>
          <span>{formatDuration(item.duration_ms)}</span>
          {item.model_used && (
            <>
              <span className="text-[var(--color-border-strong)]">|</span>
              <span className="badge-gray">{item.model_used}</span>
            </>
          )}
          {item.language && (
            <>
              <span className="text-[var(--color-border-strong)]">|</span>
              <span className="badge-blue">{item.language.toUpperCase()}</span>
            </>
          )}
          {item.is_ai_enhanced && (
            <>
              <span className="text-[var(--color-border-strong)]">|</span>
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`
                  flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider transition-all
                  ${!showOriginal 
                    ? 'bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/20 hover:border-fuchsia-500/40' 
                    : 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-muted)] border border-transparent hover:text-[var(--color-text-primary)]'}
                `}
                title={showOriginal ? 'Switch to Enhanced' : 'Switch to Original'}
              >
                {!showOriginal && (
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                )}
                {!showOriginal ? 'Enhanced' : 'Original'}
              </button>
            </>
          )}
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <button
            onClick={() => setShowExportDialog(true)}
            className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] hover:scale-110 rounded-md transition-all duration-150"
            title="Export"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </button>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] hover:scale-110 rounded-md transition-all duration-150"
            title={copied ? 'Copied!' : 'Copy to clipboard'}
          >
            {copied ? (
              <svg className="w-4 h-4 text-[var(--color-success)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </button>
          
          {/* Delete button */}
          {isDeleting ? (
            <div className="flex items-center gap-2 text-[var(--color-error)] px-2">
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-xs font-medium">Deleting...</span>
            </div>
            ) : showDeleteConfirm ? (
            <div className="flex items-center gap-1">
              <button
                onClick={handleDelete}
                className="p-1.5 text-[var(--color-error)] hover:text-white hover:bg-[var(--color-error)] hover:scale-110 rounded-md transition-all duration-150"
                title="Confirm delete"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] hover:scale-110 rounded-md transition-all duration-150"
                title="Cancel"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-muted)] hover:scale-110 rounded-md transition-all duration-150"
              title="Delete"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>
      
      {/* Text content */}
      <p className="text-[var(--color-text-primary)] whitespace-pre-wrap break-words leading-relaxed">
        {displayText}
      </p>

      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        singleRecordId={item.id}
      />
    </div>
  )
}

export default memo(HistoryItem)
