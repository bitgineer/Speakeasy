# Architecture

SpeakEasy is a desktop app plus a local server.

```
┌─────────────────────────────── Electron app ───────────────────────────────┐
│  Main process          Preload            Renderer (React)                 │
│  windows, tray         context bridge     Dashboard, Batch, Stats,         │
│  global hotkey         IPC surface        Settings pages, overlay window   │
│  spawns the backend                                                        │
└───────────────┬────────────────────────────────────────────────────────────┘
                │ spawns and health-checks
                ▼
┌─────────────────────────────── Python backend ─────────────────────────────┐
│  FastAPI (HTTP + WebSocket)                                                │
│  TranscriberService ── AudioRecorder (sounddevice)                         │
│  ModelWrapper ── faster-whisper | NeMo (Parakeet, Canary) | transformers   │
│  Services: settings, history (SQLite), batch (SQLite), export, downloads   │
└────────────────────────────────────────────────────────────────────────────┘
```

## Desktop app

- **Main process** (`gui/src/main/`): creates the main window and the recording-indicator overlay
  window, owns the tray, registers the global hotkey, and spawns the backend. It waits for
  `/api/health` before creating windows and keeps running in the tray when the window closes.
- **Overlay window**: frameless, transparent, always on top, positioned bottom center of the
  display under the cursor. It shows the idle pill, the recording pill with a timer, live
  captions, and the processing line. The window resizes itself to fit its content.
- **Renderer** (`gui/src/renderer/src/`): React app with a hash router. The main window shows the
  pages; the overlay window renders the recording indicator route. Stores keep history, settings,
  and app state. A WebSocket client receives backend events.
- **IPC**: the preload exposes a small `window.api` surface for recording control, the overlay,
  hotkey management, and the live transcript relay.

## Backend

- `server.py` defines the HTTP and WebSocket surface, holds the singleton transcriber, history,
  settings, and batch services, and broadcasts events to connected WebSocket clients.
- `core/transcriber.py` owns the recording state machine (idle, loading, ready, recording,
  transcribing, error), the audio recorder, the live caption thread, and final transcription.
- `core/models.py` wraps the model runtimes. `ModelWrapper` loads and runs one model at a time:
  - Whisper through faster-whisper (CTranslate2)
  - Parakeet and Canary through NVIDIA NeMo
  - Voxtral through transformers (optional extra)
- `services/` holds persistence and file work: settings JSON, history SQLite with full-text
  search, batch jobs in a second SQLite database, export writers, and download state.

## Recording pipeline

1. The hotkey or the overlay button posts `/api/transcribe/start`. The transcriber opens an input
   stream at the device's native rate, mono, and moves to `recording`.
2. If live captions are enabled, a background thread every `live_chunk_seconds` concatenates the
   audio recorded so far, resamples it to 16 kHz, and transcribes it. Changed text is cleaned and
   broadcast as a `live_transcript` event.
3. Stop posts `/api/transcribe/stop`. The transcriber stops the stream and the live thread, then
   transcribes the full recording. Recordings over five minutes are transcribed in two-minute
   chunks with `transcription_progress` events.
4. The result is stored in history, cleaned if enabled, broadcast as a `transcription` event, and
   pasted into the active window.

## State on disk

| Path | Contents |
|---|---|
| `~/.speakeasy/settings.json` | Settings |
| `~/.speakeasy/speakeasy.db` | History, full-text search |
| `~/.speakeasy/batch.db` | Batch jobs |
| `~/.speakeasy/model_cache/` | NeMo serialization cache |
| Hugging Face cache | Model weights |

## Events

The backend pushes JSON events over `/api/ws`: `connected`, `status`, `transcription`,
`transcription_progress`, `live_transcript`, `download_progress`, `batch_progress`, and `error`.
The full list is in [api.md](api.md).
