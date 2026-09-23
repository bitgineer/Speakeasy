# Install

SpeakEasy has two parts: a Python backend that runs the speech models, and an Electron desktop
app. The setup script prepares both.

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12 | Installed automatically by the setup script through uv |
| Node.js | 18 or newer | Needed for the desktop app |
| FFmpeg | any recent | Needed for batch and audio file transcription |
| uv | any recent | Installed automatically if missing |
| NVIDIA GPU | optional | CUDA acceleration; CPU works for every model |

Disk space matters: the backend environment is a few GB, and each speech model is between
about 40 MB (Whisper Tiny) and several GB.

## One command

Windows:

```bat
install.bat
```

macOS and Linux:

```bash
./install.sh
```

The script is idempotent. Running it again checks what already exists and skips it.

### What the script does

1. Finds or installs [uv](https://docs.astral.sh/uv/), then installs Python 3.12 with it.
2. Creates `backend/.venv` with Python 3.12 and installs the backend dependencies. It uses the
   `cuda` extra when an NVIDIA GPU is present.
3. Verifies the backend environment by importing the critical packages and, on a GPU machine,
   checking that PyTorch can see the GPU.
4. Installs the desktop dependencies with `npm install` when `gui/node_modules` is missing.
5. Checks for FFmpeg and prints install hints when it is missing.
6. Writes `~/.speakeasy/settings.json` on first run, with `device` set to `cuda` or `cpu`
   according to the hardware it found.
7. Offers to start the app.

### Flags

| Flag | Effect |
|---|---|
| `--check` | Report what is missing without changing anything |
| `--no-launch` | Install, then stop |
| `--launch` | Install, then start without asking |
| `--cpu` | Install the CPU build even when an NVIDIA GPU is present |
| `--reinstall` | Delete and rebuild the backend environment |

`start.bat` and `start.sh` are aliases for the same script with `--launch`.

## First launch

The backend loads the default model (`nvidia/parakeet-tdt-0.6b-v3`) on startup. The first launch
downloads it from Hugging Face, about 2 GB, and later launches start offline. Progress is visible
in Settings, Model, or in the terminal that is running the app.

## Manual setup

```bash
cd backend
uv venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e ".[cuda]"   # Windows with NVIDIA GPU
uv pip install --python .venv/bin/python -e ".[cuda]"           # macOS/Linux with NVIDIA GPU
uv pip install --python .venv/bin/python -e .                   # CPU only

cd ../gui
npm install
npm run dev
```

Do not use `python -m pip` inside a uv environment. uv environments do not include pip.

## Starting the app

```bash
cd gui
npm run dev      # development, with hot reload
npm run build    # production bundle
npm run preview  # run the production bundle
```

In development the Electron main process starts the backend itself and waits for
`http://127.0.0.1:8765/api/health`. If a backend is already running on that port, the app reuses
it instead of spawning a second one.

`npm run build:win` and `npm run build:linux` produce development artifacts without the backend.
Normal installs go through the setup script, which prepares the backend environment and starts
the app with `npm run dev`.

## Reinstalling

```bash
python install.py --reinstall
```

This deletes `backend/.venv` and rebuilds it. It does not touch your settings, history, or
downloaded models.
