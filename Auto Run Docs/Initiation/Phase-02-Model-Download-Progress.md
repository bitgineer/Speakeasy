# Phase 02: Model Download Progress

This phase implements a critical missing feature: visible progress tracking when downloading ASR models. Models can be hundreds of megabytes or gigabytes, and users need to see download progress, have the ability to cancel, and understand that models persist between sessions. This delivers immediate user value by eliminating the "is it frozen?" uncertainty during model loading.

## Tasks

- [ ] Extend backend with model download progress tracking:
  - Add `ModelDownloadProgress` dataclass with fields: download_id, model_name, downloaded_bytes, total_bytes, status (downloading, completed, cancelled, error), error_message
  - Create global `download_progress_store: dict[str, ModelDownloadProgress]` to track active downloads
  - Add `current_download_id: str | None` state variable to track the single active download
  - Add `cancel_download_token: threading.Event` to `ModelWrapper` class for cancellation support

- [ ] Implement progress callback in model loading:
  - Modify `ModelWrapper.load()` method to accept optional `progress_callback: Callable[[int, int], None]`
  - For HuggingFace models, hook into the `huggingface_hub` progress bars to emit progress events
  - For local model files, track file read progress if applicable
  - Ensure progress callback is called regularly during download (at least every 100MB or every 5 seconds)

- [ ] Add model download API endpoints:
  - Add `GET /api/models/download/status` endpoint returning current download progress or null
  - Add `POST /api/models/download/cancel` endpoint to cancel the active download
  - Add `GET /api/models/downloaded` endpoint returning list of already downloaded/cached models
  - Integrate with WebSocket to broadcast progress updates: `{"type": "download_progress", "downloaded": X, "total": Y, "percent": 0.XX}`

- [ ] Create model download store on frontend:
  - Add `ModelDownloadStore` to `store/model-download-store.ts`
  - Track: `isDownloading`, `downloadProgress` (0-1), `downloadedBytes`, `totalBytes`, `modelFileName`, `status`
  - Add `cancelDownload()` action
  - Add `checkDownloadedModels()` action to query cached models

- [ ] Create ModelDownloadDialog component:
  - Create `ModelDownloadDialog.tsx` as a modal overlay component
  - Show progress bar with percentage complete
  - Show downloaded/total bytes in human-readable format (MB/GB)
  - Add "Cancel Download" button (enabled only when downloading)
  - Show "Download complete!" state when finished
  - Show error state with retry button if download fails
  - Add estimated time remaining calculation based on download speed

- [ ] Update ModelSelector to show download status:
  - Add visual badge on model variants that are already downloaded
  - Show "Not downloaded - click to download" label for uncached models
  - Add file size information to each model variant
  - Disable model selection until download is complete (or allow selection with understanding it will download)

- [ ] Update Settings page integration:
  - Show download dialog immediately when user selects a model that needs downloading
  - Disable "Load Model" button while download is in progress
  - Add "Downloaded Models" section showing cached models with disk usage
  - Add "Clear Model Cache" button to remove downloaded models

- [ ] Add model persistence UI:
  - Show disk space usage for downloaded models in Settings
  - Add "Models are cached locally" info text explaining persistence
  - Add model cache location to Settings for user reference
  - Implement "Check for updates" for models (new versions available)

- [ ] Implement WebSocket progress streaming:
  - Modify backend to emit download progress via WebSocket every 1 second or 5% progress
  - Update `useWebSocket.ts` hook to handle `download_progress` message type
  - Update `app-store.ts` to sync download progress from WebSocket events

- [ ] Add error handling for download failures:
  - Handle network errors with retry option
  - Handle disk space errors with clear "Not enough disk space" message
  - Handle cancellation gracefully with cleanup of partial files
  - Add timeout for stalled downloads (no progress for 30 seconds)

- [ ] Test model download flows:
  - Test selecting a new model triggers download UI
  - Verify progress updates smoothly and accurately
  - Test cancellation works at various progress points
  - Verify downloaded models persist across app restarts
  - Test error conditions: network loss, disk full, etc.
