# Configuration

Settings are stored in `~/.speakeasy/settings.json` and loaded by the backend at startup. The
desktop app writes the file when you change a setting. You can also edit it while the app is
stopped; unknown fields are ignored and missing fields take their default.

## Settings

| Setting | Type | Default | Meaning |
|---|---|---|---|
| `model_type` | string | `parakeet` | `whisper`, `parakeet`, `canary`, or `voxtral` |
| `model_name` | string | `nvidia/parakeet-tdt-0.6b-v3` | Model identifier for the chosen type |
| `compute_type` | string | `float16` | Precision. Used by Whisper (`float16`, `int8`, `int8_float16`, `float32`) and Voxtral (`float16`, `bfloat16`, `int8`, `int4`) |
| `device` | string | `cuda` | `cuda` or `cpu` |
| `language` | string | `auto` | Recognition language, or `auto` |
| `device_name` | string or null | `null` | Microphone name; `null` uses the system default |
| `hotkey` | string | `ctrl+shift+space` | Global hotkey, for example `ctrl+shift+space` or `f8` |
| `hotkey_mode` | string | `toggle` | `toggle` or `push-to-talk` |
| `auto_paste` | boolean | `true` | Paste results into the active window. See the note below |
| `show_recording_indicator` | boolean | `true` | Show the recording overlay |
| `always_show_indicator` | boolean | `true` | Keep the overlay visible when idle |
| `theme` | string | `default` | UI theme id |
| `enable_text_cleanup` | boolean | `true` | Remove filler words and capitalize sentences |
| `custom_filler_words` | list or null | `null` | Extra filler words to remove |
| `enable_grammar_correction` | boolean | `false` | Reserved; see Known limitations |
| `grammar_model` | string | `vennify/t5-base-grammar-correction` | Reserved |
| `grammar_device` | string | `auto` | Reserved |
| `live_transcription` | boolean | `false` | Stream captions while recording |
| `live_chunk_seconds` | number | `3.0` | Live caption interval, 1 to 10 seconds |
| `live_auto_paste` | boolean | `false` | Rewrite the active text field with each live update |
| `server_port` | number | `8765` | Validated but not used to bind; the backend port comes from `--port` |

### Note on auto-paste

The desktop app's hotkey flow always requests a paste when recording stops, so dictation results
are pasted regardless of `auto_paste`. The setting applies to API callers that omit the flag.
See [Known limitations](#known-limitations).

## Files and locations

| Path | Contents |
|---|---|
| `~/.speakeasy/settings.json` | Settings |
| `~/.speakeasy/speakeasy.db` | Transcription history (SQLite, full-text search) |
| `~/.speakeasy/batch.db` | Batch jobs and per-file state |
| `~/.speakeasy/model_cache/` | NeMo model serialization cache |
| Hugging Face cache | Downloaded model weights |

## Model selection

- **Parakeet** is the default. It is fast and accurate for English on both CPU and GPU.
- **Whisper** models range from Tiny (about 39 MB) to Large-v3 (about 1.5 GB) and cover many
  languages.
- **Canary** handles transcription and translation.
- **Voxtral** needs the `voxtral` extra (`uv pip install -e ".[voxtral]"`) and a large GPU. Its
  loader currently requires CUDA.

Models download on first use and are cached. Settings, Model shows the downloaded cache and lets
you delete entries.

## Environment variables

| Variable | Effect |
|---|---|
| `SPEAKEASY_CORS_ORIGINS` | Comma-separated list of allowed CORS origins |
| `SPEAKEASY_ENV` | `production` restricts CORS to the packaged app origin |

## Known limitations

These are verified gaps in the current build. They are listed here so the docs match the code.

- The Behavior page's auto-paste toggle does not change hotkey dictation, which always pastes.
- Grammar correction has UI and settings but no working backend pipeline. The Behavior page's
  grammar buttons call endpoints that do not exist.
- The model download progress dialog is not reachable; the WebSocket subscription that drives it
  is not mounted.
- Cancelling a recording has backend and IPC support but no UI.
- Quitting from the tray may leave the process running, because the main window intercepts close
  events and there is no quitting flag.
- `server_port` does not change the port. The backend binds `--port` (default 8765) and the
  desktop app connects to 8765.
