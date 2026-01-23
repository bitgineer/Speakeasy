---
type: guide
title: Installation Guide
created: 2025-01-23
tags:
  - installation
  - windows
  - portable
  - setup
related:
  - "[[PORTABLE_MODE]]"
  - "[[TESTING]]"
  - "[[ARCHITECTURE]]"
---

# Installation Guide

This guide covers all installation methods for **faster-whisper-hotkey** on Windows.

## Overview

faster-whisper-hotkey offers three installation options:

| Method | Best For | Installation Size | Settings Location |
|--------|----------|-------------------|-------------------|
| **Windows Installer** | Most users | ~200 MB + models | `%APPDATA%\faster_whisper_hotkey\` |
| **Portable ZIP** | Testing, USB drives, no-admin setups | ~200 MB + models | `.\settings\` (next to exe) |
| **pip/uv** | Developers, Python users | Models only | `~/.config/faster_whisper_hotkey/` |

## System Requirements

### Minimum Requirements
- **OS**: Windows 10 (64-bit) or later
- **RAM**: 4 GB
- **Disk Space**: 2 GB for application + models (varies by model)
- **Internet**: Required for initial model download

### Recommended
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB or more
- **GPU**: NVIDIA GPU with CUDA support (for faster transcription)
- **Disk Space**: 10 GB for multiple models

### GPU Support (Optional)
For GPU-accelerated transcription:
- **NVIDIA GPU**: GTX 1050 or better
- **CUDA**: 11.8 or later (with cuDNN)
- **VRAM**: 4 GB recommended for large models

Check GPU compatibility:
```powershell
nvidia-smi
```

## Installation Methods

### Method 1: Windows Installer (Recommended)

The Windows installer provides the easiest installation experience with:
- Start Menu integration
- Desktop shortcut (optional)
- Automatic updates
- Proper uninstaller

#### Steps

1. **Download the installer**
   - Go to [Releases](https://github.com/blakkd/faster-whisper-hotkey/releases)
   - Download `faster-whisper-hotkey-setup-{version}.exe`

2. **Run the installer**
   - Double-click the installer
   - Click "Yes" if prompted by UAC

3. **Complete the installation wizard**
   - Read and accept the license agreement
   - Choose installation directory (default: `C:\Program Files\faster-whisper-hotkey\`)
   - Select Start Menu folder
   - Optionally create a desktop shortcut
   - Optionally enable auto-start on boot
   - Click "Install"

4. **Launch the application**
   - Check "Launch faster-whisper-hotkey" on the finish page
   - Or launch from Start Menu

5. **Complete first-run setup**
   - The setup wizard will detect your hardware
   - Choose and download a model
   - Configure your hotkey
   - Test your microphone
   - Configure privacy options

### Method 2: Portable Version

The portable version requires no installation and stores everything locally.

#### Steps

1. **Download the portable ZIP**
   - Go to [Releases](https://github.com/blakkd/faster-whisper-hotkey/releases)
   - Download `faster-whisper-hotkey-portable-{version}-windows.zip`

2. **Extract to a folder**
   - Right-click the ZIP → "Extract All..."
   - Choose a destination folder
   - Example: `C:\Apps\faster-whisper-hotkey\` or a USB drive

3. **Run the application**
   - Double-click `faster-whisper-hotkey.exe`
   - Or use `START-portable.bat` (ensures portable mode)

4. **Complete first-run setup** (same as installer)

### Method 3: pip/uv (For Developers)

Install from PyPI or source using Python package managers.

#### Prerequisites

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

#### From PyPI

```powershell
# Using uv (recommended)
uv pip install faster-whisper-hotkey

# Or using pip
pip install faster-whisper-hotkey
```

#### As a uv tool (system-wide)

```powershell
uv tool install faster-whisper-hotkey
```

#### From Source

```powershell
git clone https://github.com/blakkd/faster-whisper-hotkey
cd faster-whisper-hotkey
uv tool install .
```

#### Running

```powershell
# Launch the Flet GUI (recommended)
faster-whisper-hotkey-flet

# Or launch the Qt GUI
faster-whisper-hotkey-qt

# Or use the terminal version
faster-whisper-hotkey
```

## First-Run Setup Wizard

On first launch, you'll be guided through setup:

### Step 1: Welcome
- Introduction to the application
- Option to skip wizard (configure manually later)

### Step 2: Hardware Detection
- Automatic GPU detection (CUDA)
- CPU capability detection
- Recommended model based on your hardware

### Step 3: Model Selection
- Choose from available AI models
- See model details (size, language support, speed)
- Download progress indicator

### Step 4: Hotkey Configuration
- Choose your preferred hotkey (default: Pause)
- Test the hotkey works

### Step 5: Audio Test
- Test your microphone
- Verify audio levels
- Adjust input device if needed

### Step 6: Options
- Enable auto-start on Windows boot
- Opt-in to anonymous usage statistics

## Troubleshooting

### Installation Issues

#### "Windows protected your PC" SmartScreen Warning

This is normal for new releases. Click "More info" → "Run anyway".

#### Installer Won't Start

**Possible causes:**
- Insufficient disk space
- Antivirus blocking the installer

**Solutions:**
1. Free up at least 2 GB of disk space
2. Temporarily disable antivirus during installation
3. Run as Administrator

#### "MSVCP140.dll is missing"

Install the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).

### Runtime Issues

#### Application Won't Start

**Check Event Viewer for crash details:**
```powershell
Get-EventLog -LogName Application -Source *faster* -Newest 10
```

**Solutions:**
1. Run as Administrator once to initialize
2. Check Windows Defender is blocking the executable
3. Verify VC++ Redistributable is installed

#### Model Download Fails

**Symptoms:** Progress bar hangs or errors during download

**Solutions:**
1. Check internet connection
2. Try a different network (firewall may block HuggingFace)
3. Manually download model from HuggingFace and place in:
   - Installed: `%USERPROFILE%\.cache\huggingface\hub\`
   - Portable: `models\` next to executable

#### "No module named '_curses'" (pip installs only)

Windows doesn't include curses. Install:
```powershell
uv pip install windows-curses
```

#### "Could not find module 'libpulse.so.0'" (pip installs only)

You're running the Linux version. Ensure you have the Windows-compatible source:
```powershell
git checkout feature/supportWindows
uv tool install .
```

### Settings Issues

#### Settings Not Saving

**Installed version:**
```powershell
# Check if settings directory exists
dir "%APPDATA%\faster_whisper_hotkey"

# Check permissions
icacls "%APPDATA%\faster_whisper_hotkey"
```

**Portable version:**
```powershell
# Check settings folder next to exe
dir settings\

# Verify portable.txt exists
dir portable.txt
```

#### Reset All Settings

**Installed version:**
```powershell
# Delete settings folder
rmdir /s "%APPDATA%\faster_whisper_hotkey"
```

**Portable version:**
```powershell
# Delete settings folder
rmdir /s settings\
```

Then restart the application to run setup wizard again.

## Uninstallation

### Windows Installer

1. Open **Settings** → **Apps** → **Installed apps**
2. Search for "faster-whisper-hotkey"
3. Click the dots → **Uninstall**
4. Choose whether to delete user data:
   - **Keep**: Preserves your settings and models
   - **Delete**: Removes all app data

Or run the uninstaller directly:
```
C:\Program Files\faster-whisper-hotkey\unins000.exe
```

### Portable Version

Simply delete the folder containing the portable files:
1. Close the application
2. Delete the extracted folder
3. No traces remain on the system

### pip/uv Installation

```powershell
# If installed as a tool
uv tool uninstall faster-whisper-hotkey

# If installed with pip
pip uninstall faster-whisper-hotkey

# Optionally remove settings
rmdir /s ~/.config/faster_whisper_hotkey
```

## Updating

### Windows Installer

1. Download the new installer
2. Run it - it will automatically upgrade
3. Your settings are preserved

### Portable Version

1. Close the application
2. Download the new portable ZIP
3. Extract to a temporary location
4. Replace the old executable with the new one
5. Your settings are preserved

### pip/uv

```powershell
# Upgrade to latest version
uv pip install --upgrade faster-whisper-hotkey

# Or if installed as a tool
uv tool upgrade faster-whisper-hotkey
```

## Verification

After installation, verify everything works:

1. **Launch the application** - Should appear within 5 seconds
2. **Check the icon** - System tray icon should appear
3. **Test hotkey** - Press your hotkey, see visual feedback
4. **Test transcription** - Record a short phrase, verify text appears
5. **Check settings** - Settings are saved after restart

## Advanced Installation

### Silent Installation (Installer)

For automated deployments:
```powershell
faster-whisper-hotkey-setup-0.4.3.exe /S /D=C:\Apps\faster-whisper-hotkey
```

### Pre-Configuration (Portable)

For enterprise deployment, pre-configure settings:

1. Extract portable ZIP
2. Create `settings\transcriber_settings.json`:

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

3. Deploy to target machines

### Network Share Deployment

For organization-wide deployment:
1. Extract portable version to a network share
2. Create shortcuts to `START-portable.bat`
3. Users run from network share
4. Settings stored locally on each machine

## Related Documentation

- [[PORTABLE_MODE]] - Portable mode details and enterprise deployment
- [[TESTING]] - Testing procedures and clean system verification
- [[ARCHITECTURE]] - Application architecture and component overview
