import React, { useState, useEffect } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { apiClient } from '../api/client'
import { Button } from './ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog'
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
  const selectedFormat = FORMAT_OPTIONS.find((option) => option.value === format)

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
            <Download size={18} className="text-accent-text" aria-hidden="true" />
            {singleRecordId ? 'Export Transcription' : 'Export History'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="field">
            <label className="label" htmlFor="export-format">
              Format
            </label>
            <select
              id="export-format"
              value={format}
              onChange={(e) => setFormat(e.target.value as ExportFormat)}
              className="select"
            >
              {FORMAT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="field-hint">{selectedFormat?.description}</p>
          </div>

          {showMetadataOption && (
            <label className="check-row">
              <input
                type="checkbox"
                checked={includeMetadata}
                onChange={(e) => setIncludeMetadata(e.target.checked)}
                className="checkbox"
              />
              <span>Include metadata (duration, model, language)</span>
            </label>
          )}

          {!singleRecordId && (
            <div className="field">
              <span className="label">Date Range (optional)</span>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="input flex-1"
                  aria-label="Start date"
                  placeholder="From"
                />
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="input flex-1"
                  aria-label="End date"
                  placeholder="To"
                />
              </div>
            </div>
          )}

          {error && (
            <div
              className="rounded-control border border-danger-border bg-danger-muted p-3"
              role="alert"
            >
              <p className="text-small text-danger-text">{error}</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="button" onClick={handleExport} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 size={14} className="animate-spin" aria-hidden="true" />
                Exporting...
              </>
            ) : (
              'Export'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ExportDialog
