# SpeakEasy

<div align="center">
  <h1>SpeakEasy</h1>
  <h3>Privacy-first voice-to-text for developers</h3>
  <p>
    Local AI transcription that runs on your machine. Dictate into any app,<br/>
    transcribe audio files, and keep every word offline.
  </p>

  <p>
    <img src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-blue?style=flat-square" alt="Platform Support" />
    <img src="https://img.shields.io/github/license/bitgineer/speakeasy?style=flat-square&color=green" alt="License MIT" />
    <img src="https://img.shields.io/badge/privacy-local%20inference-success?style=flat-square" alt="Local Inference" />
    <img src="https://img.shields.io/badge/ai-whisper%20%7C%20nemo%20%7C%20voxtral-purple?style=flat-square" alt="AI Models" />
    <img src="https://github.com/bitgineer/speakeasy/workflows/Tests/badge.svg" alt="Tests" />
  </p>
</div>

---

## What it is

SpeakEasy is a desktop app and a local backend. The backend records your microphone, runs a
speech model on your hardware, and serves results over HTTP and WebSocket. The Electron app
gives you a global hotkey, a recording overlay with live captions, a searchable history, and
batch transcription of audio files.

Nothing is sent to a cloud service. The only network call is the one-time model download.

## Requirements

| Requirement | Notes |
|---|---|
| Windows 10/11, macOS, or Linux | Windows and Linux get GPU acceleration when an NVIDIA GPU is present |
| Python 3.12 | Installed automatically by the setup script through [uv](https://docs.astral.sh/uv/) |
| Node.js 18 or newer | For the desktop app |
| FFmpeg on `PATH` | Needed for audio and video file transcription; optional for live dictation |
| NVIDIA GPU | Optional. CUDA speeds up transcription; CPU works for every model |

## Quick start

Windows:

```bat
install.bat
```

macOS and Linux:

```bash
./install.sh
```

The script installs uv and Python 3.12 if needed, creates the backend environment, installs
backend and desktop dependencies, checks FFmpeg, and then offers to start the app.
`start.bat` and `start.sh` are aliases for the same script with launch enabled.

On first launch the backend downloads the default speech model (about 2 GB for Parakeet).
Later launches start offline.

### Manual setup

```bash
# Backend
cd backend
uv venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e ".[cuda]"   # Windows, NVIDIA GPU
uv pip install --python .venv/bin/python -e ".[cuda]"           # macOS/Linux
uv pip install --python .venv/bin/python -e .                   # CPU only

# Desktop app
cd ../gui
npm install
npm run dev
```

## Usage

**Dictate anywhere.** Press the global hotkey (default `Ctrl+Shift+Space`, or `F8` in the
example settings) and speak. The recording overlay appears above your windows with a timer and
live captions. Press the hotkey again to stop. The transcript is copied to your clipboard and
pasted into the active window.

Two hotkey modes are supported:

- **Toggle**: press to start, press again to stop.
- **Push-to-talk**: hold to record, release to stop. Holding for 60 seconds locks recording so
  you can release the keys; press the combination again to stop.

**Live captions.** While recording, the backend re-transcribes the audio every 1 to 10 seconds
and pushes the growing transcript to the overlay. The interval and the feature itself are in
Settings, Behavior.

**History.** Every finished transcription is stored in a local SQLite database. The Dashboard
lists and searches it, and supports export to TXT, JSON, CSV, SRT, and VTT, plus JSON import.

**Batch transcription.** The Batch page queues local audio or video files and transcribes them
one at a time with progress. FFmpeg must be installed.

**Statistics.** The Stats page summarizes counts and durations from the history database.

**System tray.** The tray icon shows ready or recording, and offers Open Dashboard, Settings,
and Quit.

## Models

| Type | Default model | Engine | Notes |
|---|---|---|---|
| Parakeet | `nvidia/parakeet-tdt-0.6b-v3` | NVIDIA NeMo | Default. Fast and accurate for English |
| Whisper | `large-v3`, `medium`, `small`, `base`, `tiny` | faster-whisper (CTranslate2) | Broad language support, sizes from 39 MB to 1.5 GB |
| Canary | `nvidia/canary-1b-v2` | NVIDIA NeMo | Speech translation and transcription |
| Voxtral | `mistralai/Voxtral-Mini-3B-2507` | transformers | Requires the `voxtral` extra and a large GPU |

The model can be changed in Settings, Model. Downloads show progress and are cached under the
Hugging Face cache, so they happen once.

## Configuration

Settings live in `~/.speakeasy/settings.json`. The app writes them when you change something in
Settings. The backend reads the file at startup.

Common settings:

| Setting | Default | Meaning |
|---|---|---|
| `model_type`, `model_name` | `parakeet`, `nvidia/parakeet-tdt-0.6b-v3` | Which model to load |
| `device` | `cuda` | `cuda` or `cpu` |
| `hotkey`, `hotkey_mode` | `ctrl+shift+space`, `toggle` | Global hotkey and its mode |
| `auto_paste` | `true` | Paste results into the active window |
| `enable_text_cleanup` | `true` | Remove filler words and capitalize sentences |
| `live_transcription` | `false` | Stream captions while recording |
| `live_chunk_seconds` | `3.0` | Live update interval, 1 to 10 seconds |

See [docs/configuration.md](docs/configuration.md) for the full list.

## Documentation

- [Install](docs/install.md): setup in detail, including a clean reinstall
- [Usage](docs/usage.md): dictation, live captions, history, batch, stats
- [Configuration](docs/configuration.md): every setting and where it lives
- [Troubleshooting](docs/troubleshooting.md): model downloads, audio devices, GPU, ports
- [Development](docs/development.md): repo layout, tests, lint, typecheck, builds
- [Architecture](docs/architecture.md): how the app, backend, and models fit together
- [HTTP and WebSocket API](docs/api.md): the real endpoint surface

## Development

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/ -q     # Windows
.venv/bin/python -m pytest tests/ -q             # macOS/Linux

cd ../gui
npm run lint
npm run typecheck
npm test
```

CI runs the backend suite, the frontend lint, typecheck and tests, and a critical-path hotspot
suite on every push to `main`.

## Troubleshooting

- **First launch seems stuck.** It is downloading the speech model. Progress appears in
  Settings, Model.
- **No audio is recorded.** Check Settings, Audio, and confirm the input device works in the
  system settings.
- **FFmpeg missing.** Install it and reopen the terminal. Batch and file transcription need it.
- **CUDA errors.** Set the device to `cpu` in Settings, Model, or reinstall with
  `python install.py --reinstall --cpu`.

More in [docs/troubleshooting.md](docs/troubleshooting.md).

## Privacy

- Speech is transcribed on your machine by local models.
- No telemetry, no accounts, no API keys.
- The app reaches the network once per model to download weights. After that it runs offline.
- History and settings stay in `~/.speakeasy/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: fork, branch, run the checks in
[Development](#development), and open a pull request.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [NVIDIA NeMo](https://github.com/NVIDIA/NeMo)
- [Mistral AI Voxtral](https://mistral.ai/)
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)
