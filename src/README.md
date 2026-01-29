# Legacy Core (faster-whisper-hotkey)

This directory contains the original Python CLI source code for the project formerly known as `faster-whisper-hotkey`.

## Status: Legacy / Maintenance

**Note:** The main development focus has shifted to the new architecture:
- **Backend:** `../backend/` (FastAPI service)
- **GUI:** `../gui/` (Electron Desktop App)

This code is preserved for backward compatibility and reference. It implements the original push-to-talk logic using global hotkeys and direct model inference.

## Usage

If you wish to use the standalone CLI tool instead of the SpeakEasy GUI:

```bash
# From root directory
python -m src.faster_whisper_hotkey
```

(Ensure dependencies from the root `pyproject.toml` are installed).
