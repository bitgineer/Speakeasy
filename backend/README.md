# SpeakEasy Backend

[← Back to Main Documentation](../README.md)

FastAPI-based backend service for SpeakEasy voice transcription.

## Quick Start

```bash
# Install dependencies
cd backend
pip install -e .

# Run the server
python -m speakeasy

# Or with options
python -m speakeasy --host 0.0.0.0 --port 8765 --verbose
```

## API Endpoints

### Health
- `GET /api/health` - Service health and status

### Transcription
- `POST /api/transcribe/start` - Start recording
- `POST /api/transcribe/stop` - Stop and transcribe
- `POST /api/transcribe/cancel` - Cancel recording

### History
- `GET /api/history` - List transcriptions (supports `?search=`, `?limit=`, `?offset=`)
- `GET /api/history/{id}` - Get specific transcription
- `DELETE /api/history/{id}` - Delete transcription
- `GET /api/history/stats` - Get statistics

### Settings
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Update settings

### Models
- `GET /api/models` - List available models
- `GET /api/models/{type}` - Get models by type
- `POST /api/models/load` - Load a model
- `POST /api/models/unload` - Unload current model
- `GET /api/models/recommend` - Get hardware-based recommendation

### Audio Devices
- `GET /api/devices` - List audio input devices
- `PUT /api/devices/{name}` - Set audio device

### WebSocket
- `WS /api/ws` - Real-time status updates

## Data Storage

All data is stored in `~/.speakeasy/`:
- `settings.json` - Application settings
- `speakeasy.db` - SQLite database (history)
- `models/` - Downloaded ASR models

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
