---
type: reference
title: Portable Mode Guide
created: 2025-01-23
tags:
  - installation
  - portable
  - windows
related:
  - "[[TESTING]]"
  - "[[ARCHITECTURE]]"
---

# Portable Mode Guide

## Overview

faster-whisper-hotkey offers two installation methods for Windows:

1. **Installed Version** - Traditional installer with Start Menu shortcuts, registry entries, and AppData storage
2. **Portable Version** - Single ZIP extraction that stores everything locally

## What is Portable Mode?

Portable mode allows you to run faster-whisper-hotkey without installing it. All settings, models, and data are stored in the application directory, making it ideal for:

- Running from a USB drive
- Testing without system modifications
- Enterprise deployments with specific configuration requirements
- Users who prefer not to install software

## Installation Methods

### Portable Version

1. Download `faster-whisper-hotkey-portable-{version}-windows.zip`
2. Extract to a folder of your choice (e.g., `C:\Apps\faster-whisper-hotkey\` or a USB drive)
3. Run `faster-whisper-hotkey.exe` or `START-portable.bat`
4. Complete the first-run setup wizard

### Installed Version

1. Download `faster-whisper-hotkey-setup-{version}.exe`
2. Run the installer
3. Follow the installation wizard
4. Launch from Start Menu or desktop shortcut

## Differences Between Modes

| Feature | Portable | Installed |
|---------|----------|-----------|
| **Installation** | No installation required | Installs to Program Files |
| **Settings Location** | `./settings/` (app directory) | `%APPDATA%/faster_whisper_hotkey/` |
| **Start Menu** | No entries | Has shortcuts |
| **Desktop Shortcut** | Manual creation | Optional during install |
| **Uninstallation** | Just delete the folder | Uses uninstaller in Add/Remove Programs |
| **Registry Entries** | None | Registration for uninstaller |
| **Auto-start on Boot** | Manual shortcut creation | Can be enabled in setup wizard |
| **Updates** | Manual download and replace | Can be automated (future) |

## File Structure

### Portable Version

```
faster-whisper-hotkey/
├── faster-whisper-hotkey.exe    # Main executable
├── portable.txt                  # Portable mode marker
├── START-portable.bat            # Optional launcher
├── README.md                     # General documentation
├── PORTABLE_README.md            # Portable-specific guide
├── LICENSE.txt                   # License file
├── settings/                     # Created on first run
│   ├── transcriber_settings.json # App settings
│   └── transcription_history.json # History
└── models/                       # Created when models are downloaded
    ├── tiny
    ├── base
    ├── small
    └── ...
```

### Installed Version

```
C:\Program Files\faster-whisper-hotkey\
├── faster-whisper-hotkey.exe

%APPDATA%\faster_whisper_hotkey\
├── transcriber_settings.json
└── transcription_history.json

C:\Users\<User>\.cache\huggingface\hub\
└── models--guillaumekln--faster-whisper-*
```

## Portable Mode Detection

The application automatically detects portable mode using one of these methods:

1. **Environment Variable** - `PORTABLE_MODE=1` (set by START-portable.bat)
2. **Marker File** - Presence of `portable.txt` next to the executable
3. **Settings Directory** - Presence of a `settings/` directory next to the executable

## Settings Storage

### Portable Mode

Settings are stored in a `settings/` subdirectory next to the executable:

- `settings/transcriber_settings.json` - Application configuration
- `settings/transcription_history.json` - Transcription history

### Installed Mode

Settings follow the Windows AppData convention:

- `%APPDATA%\faster_whisper_hotkey\transcriber_settings.json`
- `%APPDATA%\faster_whisper_hotkey\transcription_history.json`

## Model Storage

AI models are stored in the system cache by default:

- `%USERPROFILE%\.cache\huggingface\hub\`

This is shared between portable and installed versions to save disk space.

## First-Run Setup

Both portable and installed versions launch a setup wizard on first run:

1. **Hardware Detection** - Detects CUDA GPU for accelerated transcription
2. **Model Selection** - Choose and download an AI model
3. **Hotkey Configuration** - Set your preferred hotkey (default: Pause)
4. **Audio Test** - Verify microphone input works
5. **Options** - Auto-start on boot, anonymous usage statistics

## Updating

### Portable Version

1. Close the application
2. Download the new portable ZIP
3. Extract to a temporary location
4. Copy `faster-whisper-hotkey.exe` to your existing folder (replace)
5. Your settings and models are preserved

### Installed Version

1. Download the new installer
2. Run the installer
3. It will upgrade the existing installation
4. Your settings are preserved

## Uninstalling

### Portable Version

Simply delete the folder. No traces remain on the system.

### Installed Version

Use "Add or Remove Programs" in Windows Settings, or run the uninstaller from:

```
C:\Program Files\faster-whisper-hotkey\unins000.exe
```

The uninstaller prompts you to optionally delete user data.

## Troubleshooting

### Settings Not Saving

**Portable:**
- Verify the `settings/` folder exists next to the executable
- Check write permissions on the folder

**Installed:**
- Verify `%APPDATA%\faster_whisper_hotkey\` exists
- Check write permissions

### Wrong Mode Detected

If the application isn't detecting portable mode correctly:

1. Ensure `portable.txt` exists next to the executable
2. Use `START-portable.bat` to launch
3. Manually create a `settings/` folder next to the exe

### Models Not Found

Models are stored in the system cache. If you want portable model storage:

1. Create a `models/` folder next to the executable
2. Set the `model_path` in settings to this location
3. Models will be downloaded there instead

## Enterprise Deployment

For enterprise deployments, portable mode offers advantages:

1. **Silent Configuration** - Pre-configure by placing a `settings/transcriber_settings.json` file
2. **Network Share** - Run from a shared network drive
3. **No Admin Rights** - No installation requires admin privileges
4. **Easy Rollback** - Keep previous versions by renaming folders

### Example Pre-Configuration

Create a `settings/transcriber_settings.json`:

```json
{
  "device_name": "default",
  "model_type": "whisper",
  "model_name": "base",
  "compute_type": "float16",
  "device": "cpu",
  "language": "en",
  "hotkey": "pause",
  "onboarding_completed": true,
  "privacy_mode": true
}
```

## System Requirements

Both versions require:

- Windows 10 or later (64-bit)
- 4 GB RAM minimum (8 GB recommended)
- 2 GB free disk space for application
- Additional disk space for AI models:
  - tiny: ~40 MB
  - base: ~150 MB
  - small: ~500 MB
  - medium: ~1.5 GB
  - large-v3: ~3 GB

## Related Documentation

- [[TESTING]] - Testing procedures for portable and installed versions
- [[ARCHITECTURE]] - Application architecture details
- [[IMPLEMENTATION_GUIDES]] - Implementation and development guides
