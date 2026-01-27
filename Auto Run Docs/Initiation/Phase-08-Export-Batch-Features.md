# Phase 08: Export and Batch Features

This phase adds high-value functionality for users who need to work with their transcriptions outside the app. Export functionality allows users to save transcriptions in various formats, while batch processing enables efficient handling of multiple audio files. These features make SpeakEasy more practical for professional use cases.

## Tasks

- [ ] Design export data model and API:
  - Add export formats to types: TXT, JSON, CSV, SRT, VTT
  - Create `ExportRequest` Pydantic model with format and filters
  - Add `GET /api/history/export` endpoint accepting format parameter
  - Add `POST /api/history/export` endpoint for filtered exports
  - Return file with appropriate Content-Type and headers

- [ ] Implement backend export functionality:
  - Create `backend/speakeasy/services/export.py` module
  - Implement `to_txt()` export - plain text format
  - Implement `to_json()` export - structured data with metadata
  - Implement `to_csv()` export - spreadsheet-compatible format
  - Implement `to_srt()` export - SubRip subtitle format with timestamps
  - Implement `to_vtt()` export - WebVTT subtitle format
  - Add export date range and search filtering

- [ ] Add export UI components:
  - Create `ExportDialog.tsx` modal component
  - Add format selection dropdown with format descriptions
  - Add date range picker for filtering
  - Add "Include metadata" checkbox for JSON/CSV
  - Add export button that triggers file download
  - Show loading state during export generation

- [ ] Integrate export into Dashboard and Settings:
  - Add "Export All" button to Dashboard header
  - Add individual export button to each HistoryItem overflow menu
  - Add export keyboard shortcut (Ctrl/Cmd+E)
  - Add export option to context menu on history items

- [ ] Implement batch transcription API:
  - Add `POST /api/transcribe/batch` endpoint
  - Accept list of file paths or uploaded files
  - Queue files for sequential processing
  - Return batch job ID for progress tracking
  - Add `GET /api/transcribe/batch/{job_id}` status endpoint

- [ ] Add batch transcription backend service:
  - Create `backend/speakeasy/services/batch.py` module
  - Implement job queue with SQLite persistence
  - Implement sequential file processing with progress updates
  - Handle errors per-file without stopping entire batch
  - Broadcast progress via WebSocket
  - Support cancellation of in-progress batches

- [ ] Create batch transcription UI:
  - Create `BatchTranscriptionPage.tsx` new route
  - Add file picker/drop zone for selecting audio files
  - Show list of selected files with sizes and durations
  - Add "Start Batch" button
  - Show progress bar with file-by-file progress
  - Show results summary when complete (success, failed, skipped)

- [ ] Add batch results handling:
  - Create results view with per-file status
  - Allow exporting batch results
  - Allow retrying failed files
  - Add individual file preview with transcription
  - Add "Save all to history" option

- [ ] Add import functionality:
  - Create `POST /api/history/import` endpoint
  - Accept JSON export files for re-importing
  - Merge with existing history or replace option
  - Validate imported data format
  - Add import UI to Settings page

- [ ] Test export and batch features:
  - Test each export format produces valid output
  - Test export filtering by date and search
  - Test batch processing with multiple files
  - Test batch cancellation at various stages
  - Test import of previously exported data
  - Test error handling for corrupt/invalid files

- [ ] Add documentation for new features:
  - Update README with export and batch feature descriptions
  - Add help tooltips explaining each export format
  - Add sample export outputs for user reference
  - Document batch transcription workflow
