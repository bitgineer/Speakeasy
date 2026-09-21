/**
 * Data Settings Page
 * 
 * Import/Export transcription history.
 */

import { useRef, useState } from 'react'
import ExportDialog from '../../components/ExportDialog'
import { apiClient } from '../../api/client'

export default function DataSettings(): JSX.Element {
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [importStatus, setImportStatus] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [mergeImport, setMergeImport] = useState(true)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsImporting(true)
    setImportStatus(null)

    try {
      const text = await file.text()
      const data = JSON.parse(text)

      if (!data.transcriptions || !Array.isArray(data.transcriptions)) {
        throw new Error('Invalid file format: missing "transcriptions" array')
      }

      const result = await apiClient.importHistory({
        data,
        merge: mergeImport
      })

      setImportStatus({
        message: `Successfully imported ${result.imported} records (skipped ${result.skipped})`,
        type: 'success'
      })
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      setImportStatus({
        message: err instanceof Error ? err.message : 'Import failed',
        type: 'error'
      })
    } finally {
      setIsImporting(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Data Management</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Import and export your transcription history</p>
      </div>

      <div className="space-y-6">
        {/* Import */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Import History</h2>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            Import transcription history from a JSON file exported from SpeakEasy.
          </p>
          
          <div className="flex flex-col gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={mergeImport}
                onChange={(e) => setMergeImport(e.target.checked)}
                disabled={isImporting}
                className="w-4 h-4 text-[var(--color-accent)] bg-[var(--color-bg-secondary)] border-[var(--color-border)] rounded focus:ring-[var(--color-accent)]"
              />
              <span className="text-sm text-[var(--color-text-secondary)]">Merge with existing history</span>
            </label>
            
            <div className="flex items-center gap-3">
              <input
                type="file"
                ref={fileInputRef}
                accept=".json"
                onChange={handleImport}
                className="hidden"
                disabled={isImporting}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isImporting}
                className="btn-secondary text-sm"
              >
                {isImporting ? 'Importing...' : 'Select JSON File'}
              </button>
              {importStatus && (
                <span className={`text-sm ${importStatus.type === 'success' ? 'text-[var(--color-success)]' : 'text-[var(--color-error)]'}`}>
                  {importStatus.message}
                </span>
              )}
            </div>
          </div>
        </section>

        {/* Export */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Export History</h2>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            Export your transcription history to a JSON file for backup or transfer.
          </p>
          <button
            onClick={() => setShowExportDialog(true)}
            className="btn-secondary text-sm"
          >
            Export All History
          </button>
        </section>

        {/* Data Privacy Notice */}
        <section className="card p-4">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Privacy</h2>
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-[var(--color-info)] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <div>
              <p className="text-sm text-[var(--color-text-secondary)]">
                All transcription data is stored locally on your device. Your data never leaves your computer
                and is not sent to any external servers. Exported files contain your transcription text and metadata.
              </p>
            </div>
          </div>
        </section>
      </div>

      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
      />
    </div>
  )
}
