/**
 * Data Settings Page
 * 
 * Import/Export transcription history.
 */

import { useRef, useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import ExportDialog from '../../components/ExportDialog'
import { Button } from '../../components/ui/button'
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
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Settings / data</p>
          <h1>Data Management</h1>
          <p className="page-subtitle">Import and export your transcription history.</p>
        </div>
      </header>

      <div className="settings-stack">
        {/* Import */}
        <section className="card settings-panel" aria-labelledby="import-title">
          <div className="settings-head">
            <div>
              <h2 id="import-title">Import history</h2>
              <p className="panel-subtitle">
                Import transcription history from a JSON file exported from SpeakEasy.
              </p>
            </div>
          </div>
          
          <div className="settings-rows">
            <label className="check-row">
              <input
                type="checkbox"
                checked={mergeImport}
                onChange={(e) => setMergeImport(e.target.checked)}
                disabled={isImporting}
                className="checkbox"
              />
              <span>Merge with existing history</span>
            </label>
            
            <div className="input-row">
              <input
                type="file"
                ref={fileInputRef}
                accept=".json"
                onChange={handleImport}
                className="hidden"
                disabled={isImporting}
              />
              <Button
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={isImporting}
              >
                {isImporting ? 'Importing...' : 'Select JSON file'}
              </Button>
              {importStatus && (
                <span
                  className={
                    importStatus.type === 'success'
                      ? 'text-success-text text-small'
                      : 'text-danger-text text-small'
                  }
                  role="status"
                >
                  {importStatus.message}
                </span>
              )}
            </div>
          </div>
        </section>

        {/* Export */}
        <section className="card settings-panel" aria-labelledby="export-title">
          <div className="settings-head">
            <div>
              <h2 id="export-title">Export history</h2>
              <p className="panel-subtitle">
                Export your transcription history to a JSON file for backup or transfer.
              </p>
            </div>
          </div>
          <Button variant="secondary" onClick={() => setShowExportDialog(true)}>
            Export all history
          </Button>
        </section>

        {/* Data Privacy Notice */}
        <section className="card settings-panel" aria-labelledby="privacy-title">
          <div className="settings-head">
            <h2 id="privacy-title">Privacy</h2>
          </div>
          <div className="privacy-note">
            <ShieldCheck size={18} strokeWidth={1.75} aria-hidden="true" />
            <p>
              All transcription data is stored locally on your device. Your data never leaves your
              computer and is not sent to any external servers. Exported files contain your
              transcription text and metadata.
            </p>
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
