# Backend Services

This directory contains backend services for SpeakEasy:

## History (`history.py`)
Transcription history management using SQLite with FTS5.

Features:
- Async database operations with `aiosqlite`
- Full-text search via FTS5 (SQLite extension)
- Cursor-based pagination for efficient large datasets
- Field projection to reduce payload size
- Statistics (total, today, this week, this month)
- Import/Export in multiple formats (JSON, TXT, CSV, SRT, VTT)

Database schema:
```sql
CREATE TABLE transcriptions (
  id TEXT PRIMARY KEY,
  text TEXT NOT NULL,
  duration_ms INTEGER,
  model_used TEXT,
  language TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  original_text TEXT  -- For AI enhancement comparison
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE transcriptions_fts
USING fts5(text, content=transcriptions, content_rowid=rowid);
```

API:
- `add()` - Add new transcription
- `get(id)` - Get single record
- `list(limit, offset, search, cursor, fields)` - List with pagination and search
- `delete(id)` - Delete record
- `clear()` - Delete all records
- `get_stats()` - Get statistics
- `update_text(id, new_text, original_text)` - Update after AI enhancement
- `initialize()` - Create tables and run migrations
- `close()` - Close database connection

## Batch (`batch.py`)
Batch transcription job management.

Features:
- Queue-based processing of multiple audio files
- Job persistence in SQLite (`batch.db`)
- Per-file error handling with 1 automatic retry
- GPU error detection and automatic model reload
- Real-time progress reporting via WebSocket
- Job cancellation and retry (individual files or all)

Job states:
- pending: Queued, waiting to start
- processing: Currently transcribing
- completed: All files finished
- cancelled: User cancelled
- failed: Some files failed

## Settings (`settings.py`)
Application settings management.

Features:
- JSON file storage (`~/.speakeasy/settings.json`)
- Auto-save on update
- Default values
- Settings validation
- Partial updates supported

Settings:
```typescript
{
  model_type: string,        // "whisper" | "parakeet" | "canary" | "voxtral"
  model_name: string,         // e.g., "whisper-base"
  device: string,              // "cuda" | "cpu"
  compute_type: string,        // e.g., "float16"
  language: string,            // Language code or "auto"
  device_name: string,         // Audio device name
  hotkey: string,             // e.g., "ctrl+shift+space"
  hotkey_mode: string,         // "toggle" | "push-to-talk"
  auto_paste: boolean,
  show_recording_indicator: boolean,
  always_show_indicator: boolean,
  theme: string,               // Theme name
  enable_text_cleanup: boolean,
  custom_filler_words: string[],
  enable_grammar_correction: boolean,
  grammar_model: string,        // LLM model for correction
  grammar_device: string,       // "cuda" | "cpu" | "auto"
  server_port: number           // Backend server port (default: 8765)
}
```

## Export (`export.py`)
Multi-format export service.

Supported formats:
- **JSON**: Full metadata, suitable for backup/import
- **TXT**: Plain text only
- **CSV**: Tabular data with metadata
- **SRT**: SubRip subtitle format with timestamps
- **VTT**: WebVTT subtitle format

API:
- `export(records, format, include_metadata)` - Export records to string
- Returns: `(content, filename, content_type)`

## Download State (`download_state.py`)
Model download progress tracking.

Features:
- Download state management (pending, downloading, completed, cancelled, error)
- Progress tracking: bytes downloaded, total bytes, percent
- Speed calculation: bytes per second
- ETA calculation: estimated time remaining
- Stall detection: 30s timeout
- Cancellation support
- Thread-safe state access

States:
- pending: Queued, not started
- downloading: Active download with progress updates
- completed: Successfully downloaded
- cancelled: User cancelled
- error: Download failed (stalled or network error)

WebSocket events:
```typescript
{
  type: "download_progress",
  status: "downloading",
  model_name: string,
  bytes: number,
  total: number,
  percent: number,  // 0-100
  speed: number,     // MB/s
  eta: number        // seconds remaining
}
```
