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

## Running Tests

We have **387 tests** ensuring code quality:

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ -v --cov=speakeasy --cov-report=term-missing

# Run specific test files
uv run pytest tests/test_transcriberservice*.py -v
uv run pytest tests/test_historyservice*.py -v

# Run tests by priority
uv run pytest tests/test_transcriberservice__set_state.py -v  # P0 Critical
uv run pytest tests/test_exportservice*.py -v                  # P1 High
```

### Test Coverage

- **P0 - Critical** (30 tests): State machine, transcription, database operations
- **P1 - High** (8 tests): Batch processing, exports, settings
- **P2 - Medium** (3 tests): Utilities, configuration
- **P3 - Low** (1 test): Legacy support

Current status: **302 tests passing** (78% success rate)

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
