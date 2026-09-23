/**
 * HistoryItem Component
 *
 * Displays a single transcription record with copy, export, and delete actions.
 */

import { useState, memo, useEffect, useLayoutEffect, useId, useRef } from 'react'
import { Check, Copy, Download, Loader2, Trash2, X } from 'lucide-react'
import { cn } from '../lib/utils'
import type { TranscriptionRecord } from '../api/types'
import ExportDialog from './ExportDialog'
import { Button } from './ui/button'

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
  const [expanded, setExpanded] = useState(false)
  const [overflowing, setOverflowing] = useState(false)
  const bodyId = useId()
  const bodyRef = useRef<HTMLParagraphElement>(null)
  const prevTextRef = useRef(item.text)

  // Flash effect only for the newest transcription (first item) when text updates
  useEffect(() => {
    // Only flash if this is the newest item (index 0) and text actually changed
    if (index !== 0 || prevTextRef.current === item.text) return
    setIsFlashing(true)
    const timer = setTimeout(() => setIsFlashing(false), 2000)
    prevTextRef.current = item.text
    return () => clearTimeout(timer)
  }, [item.text, index])

  // Get the text to display based on toggle state
  const displayText = showOriginal && item.original_text ? item.original_text : item.text

  // The full value stays reachable: the toggle appears exactly when the clamped
  // paragraph hides content.
  useLayoutEffect(() => {
    const body = bodyRef.current
    if (!body || expanded) return
    setOverflowing(body.scrollHeight > body.clientHeight + 1)
  }, [displayText, expanded])

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
    <article className={cn('card record', isFlashing && 'record-flash')}>
      <div className="record-head">
        <div className="record-meta">
          <time dateTime={item.created_at} title={new Date(item.created_at).toLocaleString()}>
            {formatDate(item.created_at)}
          </time>
          <span>{formatDuration(item.duration_ms)}</span>
          {item.model_used && <span className="pill">{item.model_used}</span>}
          {item.language && <span className="pill">{item.language.toUpperCase()}</span>}
        </div>

        <div className="record-actions">
          {item.is_ai_enhanced && item.original_text && (
            <div className="segmented" role="group" aria-label="Text version">
              <button
                type="button"
                aria-pressed={!showOriginal}
                onClick={() => setShowOriginal(false)}
                title="Show processed text"
              >
                Processed
              </button>
              <button
                type="button"
                aria-pressed={showOriginal}
                onClick={() => setShowOriginal(true)}
                title="Show original text"
              >
                Original
              </button>
            </div>
          )}

          <Button
            variant="ghost"
            size="sm"
            className="px-2"
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy to clipboard'}
          >
            {copied ? (
              <Check size={14} className="text-success-text" aria-hidden="true" />
            ) : (
              <Copy size={14} aria-hidden="true" />
            )}
            {copied ? 'Copied' : 'Copy'}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="px-2"
            onClick={() => setShowExportDialog(true)}
            title="Export"
          >
            <Download size={14} aria-hidden="true" />
            <span className="sr-only">Export</span>
          </Button>

          {isDeleting ? (
            <span className="flex items-center gap-2 px-2 text-caption text-danger-text">
              <Loader2 size={14} className="animate-spin" aria-hidden="true" />
              Deleting...
            </span>
          ) : showDeleteConfirm ? (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="px-2 hover:text-danger-text"
                onClick={handleDelete}
                title="Confirm delete"
              >
                <Check size={14} aria-hidden="true" />
                <span className="sr-only">Confirm delete</span>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="px-2"
                onClick={() => setShowDeleteConfirm(false)}
                title="Cancel"
              >
                <X size={14} aria-hidden="true" />
                <span className="sr-only">Cancel delete</span>
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="px-2 hover:text-danger-text"
              onClick={() => setShowDeleteConfirm(true)}
              title="Delete"
            >
              <Trash2 size={14} aria-hidden="true" />
              <span className="sr-only">Delete</span>
            </Button>
          )}
        </div>
      </div>

      <p ref={bodyRef} id={bodyId} className={cn('record-body', expanded && 'expanded')}>
        {displayText}
      </p>

      <div className="record-foot">
        {(overflowing || expanded) && (
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
            aria-controls={bodyId}
          >
            {expanded ? 'Show less' : 'Show full text'}
          </button>
        )}
      </div>

      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        singleRecordId={item.id}
      />
    </article>
  )
}

export default memo(HistoryItem)
