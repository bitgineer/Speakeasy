import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import type { ExportFormat } from '../api/types'

interface ExportDialogProps {
  isOpen: boolean
  onClose: () => void
  singleRecordId?: string
}

const FORMAT_OPTIONS: { value: ExportFormat; label: string; description: string }[] = [
  { value: 'txt', label: 'Plain Text', description: 'Simple text format, one transcription per block' },
  { value: 'json', label: 'JSON', description: 'Structured data with metadata, ideal for backup/import' },
  { value: 'csv', label: 'CSV', description: 'Spreadsheet compatible, opens in Excel/Sheets' },
  { value: 'srt', label: 'SRT', description: 'SubRip subtitle format for video players' },
  { value: 'vtt', label: 'VTT', description: 'WebVTT subtitle format for web videos' },
]

const ExportDialog: React.FC<ExportDialogProps> = ({ isOpen, onClose, singleRecordId }) => {
  const [format, setFormat] = useState<ExportFormat>('json')
  const [includeMetadata, setIncludeMetadata] = useState(true)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  const handleExport = async () => {
    setIsLoading(true)
    setError(null)

    try {
      let blob: Blob

      if (singleRecordId) {
        blob = await apiClient.exportHistoryFiltered({
          format,
          include_metadata: includeMetadata,
          record_ids: [singleRecordId],
        })
      } else if (startDate || endDate) {
        blob = await apiClient.exportHistoryFiltered({
          format,
          include_metadata: includeMetadata,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        })
      } else {
        blob = await apiClient.exportHistory(format, includeMetadata)
      }

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `speakeasy_export_${new Date().toISOString().slice(0, 10)}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  const showMetadataOption = format === 'json' || format === 'csv'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-labelledby="export-dialog-title"
    >
      <div className="w-full max-w-md transform overflow-hidden rounded-2xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)] p-6 text-left align-middle shadow-xl transition-all">
        <h3
          id="export-dialog-title"
          className="text-lg font-medium leading-6 text-[var(--color-text-primary)] mb-4 flex items-center gap-2"
        >
          <svg className="w-6 h-6 text-[var(--color-accent)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          {singleRecordId ? 'Export Transcription' : 'Export History'}
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
              Format
            </label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as ExportFormat)}
              className="w-full px-3 py-2 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
            >
              {FORMAT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-[var(--color-text-muted)]">
              {FORMAT_OPTIONS.find((o) => o.value === format)?.description}
            </p>
          </div>

          {showMetadataOption && (
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeMetadata}
                onChange={(e) => setIncludeMetadata(e.target.checked)}
                className="w-4 h-4 text-[var(--color-accent)] bg-[var(--color-bg-tertiary)] border-[var(--color-border)] rounded focus:ring-[var(--color-accent)]"
              />
              <span className="text-sm text-[var(--color-text-secondary)]">Include metadata (duration, model, language)</span>
            </label>
          )}

          {!singleRecordId && (
            <>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                  Date Range (optional)
                </label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="flex-1 px-3 py-2 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
                    placeholder="From"
                  />
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="flex-1 px-3 py-2 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
                    placeholder="To"
                  />
                </div>
              </div>
            </>
          )}

          {error && (
            <div className="bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg p-3">
              <p className="text-sm text-[var(--color-error)]">{error}</p>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="inline-flex justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-tertiary)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-bg-elevated)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] transition-colors"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="inline-flex justify-center rounded-lg border border-transparent bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-[var(--color-text-on-accent)] hover:bg-[var(--color-accent-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleExport}
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Exporting...
              </span>
            ) : (
              'Export'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ExportDialog
