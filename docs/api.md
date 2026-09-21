# HTTP and WebSocket API

The backend serves on `http://127.0.0.1:8765` by default. Change it with
`python -m speakeasy --port <port>`.

There is no response envelope. Routes return their data directly, and errors use standard HTTP
status codes with a `detail` field.

## Recording

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/transcribe/start` | Start recording from the microphone |
| POST | `/api/transcribe/stop` | Stop, transcribe, and return the result |
| POST | `/api/transcribe/cancel` | Discard the recording |

`POST /api/transcribe/stop` accepts `{auto_paste, language, instruction}` and returns
`{id, text, duration_ms, model_used, language}`. When `auto_paste` is omitted, the persisted
setting decides whether the result is pasted.

## History

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/history` | List and search, with `limit`, `offset`, `search`, `cursor`, `fields` |
| GET | `/api/history/stats` | Counts and durations |
| GET | `/api/history/export` | Export everything (`format`, `include_metadata`) |
| GET | `/api/history/{id}` | One record |
| DELETE | `/api/history/{id}` | Delete one record |
| POST | `/api/history/export` | Filtered export (`format`, date range, search, ids) |
| POST | `/api/history/import` | Import a JSON export, with `merge` |

Export formats: `txt`, `json`, `csv`, `srt`, `vtt`.

## Batch

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/transcribe/batch` | Create a job from local `file_paths` |
| GET | `/api/transcribe/batch` | List jobs |
| GET | `/api/transcribe/batch/{id}` | Job status |
| POST | `/api/transcribe/batch/{id}/cancel` | Cancel |
| POST | `/api/transcribe/batch/{id}/retry` | Retry failed files |
| DELETE | `/api/transcribe/batch/{id}` | Delete a job |

## Settings and devices

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/settings` | Current settings |
| PUT | `/api/settings` | Partial update |
| GET | `/api/devices` | Input devices and the current one |
| PUT | `/api/devices/{name}` | Select an input device (`default` for the system default) |

## Models

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/models` | Catalog and current model |
| GET | `/api/models/types` | Model type names |
| GET | `/api/models/recommend` | Hardware-based recommendation |
| POST | `/api/models/load` | Load or download a model |
| POST | `/api/models/unload` | Unload |
| GET | `/api/models/download/status` | Download progress |
| POST | `/api/models/download/cancel` | Cancel a download |
| GET | `/api/models/downloaded` | Cached models |
| GET | `/api/models/cache` | Cache size and contents |
| DELETE | `/api/models/cache` | Clear the cache, or one model |
| GET | `/api/models/{type}` | Models, languages, and compute types for a type |

## Health

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Status, model state, GPU information |

## WebSocket

Connect to `ws://127.0.0.1:8765/api/ws`. On connect the server sends
`{"type": "connected", "state": ..., "model_loaded": ...}`.

Server events:

| Type | Payload |
|---|---|
| `status` | `state`, `recording` |
| `transcription` | `id`, `text`, `duration_ms` |
| `transcription_progress` | chunk progress for long recordings |
| `live_transcript` | `text` |
| `download_progress` | model download progress |
| `batch_progress` | job and per-file progress |
| `error` | `message` |

Clients may send the text `ping`; the server answers `pong`. The server also sends `ping` after
30 seconds of inactivity.

## Rate limits

Some routes are rate limited per client: stop (10/min), import (5/min), batch create (10/min),
settings update (20/min), model load (5/min), cache delete (5/min).

## CORS

Allowed origins are a fixed list for local development, or the packaged app origin in production.
Override with the `SPEAKEASY_CORS_ORIGINS` environment variable (comma-separated).
