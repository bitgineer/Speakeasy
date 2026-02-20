# SpeakEasy Backend

[← Back to Main Documentation](../README.md)

FastAPI-based backend service for SpeakEasy voice transcription.

## Requirements

- **Python**: 3.10 to 3.12
- **FFmpeg**: Required for audio processing. Ensure it is installed and added to your system PATH.
  - Windows: `winget install Gyan.FFmpeg`
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
- **Windows Users**: Microsoft Visual C++ 14.0 or greater is required for building some dependencies (like `texterrors`).
  - Install "Desktop development with C++" workload from [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

## Quick Start

We use [uv](https://github.com/astral-sh/uv) for fast Python package management.

```bash
# Install uv if not already installed
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies
cd backend
uv sync --all-extras --dev

# Run the server
uv run python -m speakeasy

# Or with options
uv run python -m speakeasy --host 0.0.0.0 --port 8765 --verbose
```

Alternatively, activate the virtual environment first:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m speakeasy
```

## API Endpoints

### Health
- `GET /api/health` - Service health and status

### Transcription
- `POST /api/transcribe/start` - Start recording
- `POST /api/transcribe/stop` - Stop and transcribe (supports language, instruction, grammar_correction, auto_paste)
- `POST /api/transcribe/cancel` - Cancel recording
- `POST /api/transcribe/batch` - Create batch transcription job for multiple files
- `GET /api/transcribe/batch` - List all batch jobs
- `GET /api/transcribe/batch/{job_id}` - Get batch job status
- `POST /api/transcribe/batch/{job_id}/cancel` - Cancel batch job
- `POST /api/transcribe/batch/{job_id}/retry` - Retry failed files in batch job
- `DELETE /api/transcribe/batch/{job_id}` - Delete batch job

### History
- `GET /api/history` - List transcriptions (supports `?search=`, `?limit=`, `?offset=`, `?cursor=`, `?fields=`)
- `GET /api/history/{id}` - Get specific transcription
- `DELETE /api/history/{id}` - Delete transcription
- `GET /api/history/stats` - Get statistics
- `POST /api/history/export` - Export history (JSON, TXT, CSV, SRT, VTT formats; supports date range, search, specific records)
- `POST /api/history/import` - Import transcriptions from JSON (merge or replace mode)

### Settings
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Update settings

### Models
- `GET /api/models` - List available models and current model
- `GET /api/models/types` - Get available model types
- `GET /api/models/{type}` - Get models by type (languages, compute types, info)
- `POST /api/models/load` - Load a model (supports download progress tracking)
- `POST /api/models/unload` - Unload current model
- `GET /api/models/recommend` - Get hardware-based recommendation
- `GET /api/models/download/status` - Get current download progress
- `POST /api/models/download/cancel` - Cancel current model download
- `GET /api/models/downloaded` - List downloaded/cached models
- `GET /api/models/cache` - Get model cache information and disk usage
- `DELETE /api/models/cache` - Clear model cache (specific model or all)

### Audio Devices
- `GET /api/devices` - List audio input devices
- `PUT /api/devices/{name}` - Set audio device

### WebSocket
- `WS /api/ws` - Real-time status updates

  Events:
  - `status` - Recording state changes, model loading status
  - `transcription` - New transcription completed
  - `transcription_progress` - Long transcription progress (chunk-based)
  - `download_progress` - Model download progress (bytes, percent, speed, ETA)
  - `batch_progress` - Batch transcription job progress
  - `error` - Error notifications

## Features

### Batch Transcription
Process multiple audio files in a queue:
- Job creation with file paths
- Sequential processing with progress tracking
- Per-file error handling with retry (1 retry per file)
- GPU error detection and automatic model reload
- Job cancellation (skips remaining files)
- SQLite persistence (`~/.speakeasy/batch.db`)
- WebSocket progress broadcasts
- Retry failed files individually or all

### History Import/Export
Export transcription history in multiple formats:
- **JSON** - Full metadata, suitable for backup/import
- **TXT** - Plain text only
- **CSV** - Tabular data with metadata
- **SRT** - SubRip subtitle format
- **VTT** - WebVTT subtitle format

Import options:
- Merge with existing history (skip duplicates by ID)
- Replace all history (clear and import)

Filtering:
- Date range (ISO format)
- Search query (full-text)
- Specific record IDs

## Data Storage

All data is stored in `~/.speakeasy/`:
- `settings.json` - Application settings
- `speakeasy.db` - SQLite database (history)
- `batch.db` - SQLite database (batch jobs)
- `models/` - Downloaded ASR models (HuggingFace cache at `~/.cache/huggingface/hub`)

## Supported Models

| Type | Model | VRAM | Use Case |
|------|-------|------|----------|
| parakeet | nvidia/parakeet-tdt-0.6b-v3 | ~4GB | Fast, accurate, 25 EU languages |
| canary | nvidia/canary-1b-v2 | ~6GB | Translation support |
| whisper | tiny to large-v3-turbo | 1-10GB | Wide language support |
| voxtral | mistralai/Voxtral-Mini-3B-2507 | ~10GB | Advanced Q&A capabilities |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format .
ruff check --fix .
```

## Model Download Progress
Model downloads support real-time progress tracking:
- Progress callbacks broadcast download status via WebSocket
- Stall detection (30s timeout)
- Cancellation support
- Download statistics: bytes, percent, speed, ETA

Download states:
- `pending` - Queued
- `downloading` - Active download with progress updates
- `completed` - Successfully downloaded
- `cancelled` - User cancelled
- `error` - Download failed (stalled or network error)

## Rate Limiting
Endpoints with rate limiting:
- `POST /api/transcribe/stop` - 10/minute
- `POST /api/models/load` - 5/minute
- `POST /api/history/import` - 5/minute
- `PUT /api/settings` - 20/minute
- `DELETE /api/models/cache` - 5/minute

## CORS Configuration
Development mode allows localhost on ports 3000, 5173, 8080.
Production mode allows `app://` (Electron) only.

Override with `SPEAKEASY_CORS_ORIGINS` environment variable (comma-separated).
