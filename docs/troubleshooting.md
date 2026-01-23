---
type: guide
title: Troubleshooting Guide
created: 2025-01-23
tags:
  - troubleshooting
  - errors
  - diagnostics
  - support
related:
  - "[[installation]]"
  - "[[known-issues]]"
  - "[[TESTING]]"
---

# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with faster-whisper-hotkey.

## Quick Diagnostics

### Check Application Status

```powershell
# Check if the process is running
Get-Process | Where-Object {$_.ProcessName -like "*faster*"}

# Check system tray icon status
# Look for the microphone icon in your system tray
```

### Enable Debug Logging

Create a batch file `debug_mode.bat` next to the executable:

```batch
@echo off
set FWH_DEBUG=1
set FWH_LOG_LEVEL=DEBUG
faster-whisper-hotkey.exe
```

Log files are saved to:
- **Installed**: `%APPDATA%\faster_whisper_hotkey\logs\`
- **Portable**: `logs\` next to executable

---

## Common Error Messages

### Model Download Errors

#### "Model Download Failed"

**Symptoms:**
- Download progress bar stops or errors
- "Connection timeout" message
- "SSL certificate verification failed"

**Solutions:**
1. Check internet connection
2. Verify firewall isn't blocking HuggingFace (huggingface.co)
3. Try downloading again - automatic retry is enabled (3 attempts)
4. Manually download from HuggingFace:
   - Go to https://huggingface.co/guillaumekln/faster-whisper-large-v3
   - Download model files
   - Place in `%USERPROFILE%\.cache\huggingface\hub\`

**Related:** `error_handling.py:ModelDownloadError`

---

#### "Out of Disk Space"

**Symptoms:**
- Download fails with disk space error
- Model files are large (1-3 GB each)

**Solutions:**
1. Free up disk space (need at least 5 GB for large models)
2. Use a smaller model (tiny, base, small)
3. Change cache location with environment variable:
   ```powershell
   set HF_HOME=D:\Models\huggingface
   ```

---

### Audio Device Errors

#### "No Audio Device Found"

**Symptoms:**
- Application shows "No microphone available"
- Recording button is disabled
- Error on startup

**Solutions:**
1. Check microphone is connected and recognized by Windows:
   ```powershell
   Get-PnpDevice -Class Audio | Where-Object {$_.Status -eq "OK"}
   ```
2. Set default recording device in Windows Sound settings
3. Check Privacy settings:
   - Settings → Privacy → Microphone → Allow apps to access
4. Try a different USB port (for USB microphones)

**Automatic Fallback:**
The app attempts to reconnect with alternative devices automatically. Check logs for:
```
Fell back to audio device: [device name]
```

**Related:** `error_handling.py:AudioDeviceError`, `transcriber.py:audio_device_fallback`

---

#### "Audio Device Disconnected During Recording"

**Symptoms:**
- Recording stops unexpectedly
- Error message about device disconnect

**Solutions:**
1. Reconnect the microphone
2. Check USB cable connection
3. Update audio drivers
4. Try a different USB port

**Automatic Recovery:**
The app attempts automatic reconnection with fallback devices.

---

### GPU Errors

#### "CUDA Out of Memory"

**Symptoms:**
- Transcription fails with OOM error
- Application crashes during transcription

**Solutions:**
1. Use a smaller model (tiny, base, small instead of medium/large)
2. Close other GPU-intensive applications
3. Reduce compute type in settings:
   - Change from `float16` to `int8` or `int8_float16`
4. The app automatically falls back to CPU if GPU fails

**Automatic CPU Fallback:**
The app will attempt CPU transcription if GPU fails. Check logs for:
```
GPU initialization failed: [error]. Falling back to CPU...
```

**Related:** `error_handling.py:GPUInitializationError`, `models.py:gpu_fallback`

---

#### "GPU Not Detected"

**Symptoms:**
- Settings show "CPU" as only device option
- Transcription is slow

**Solutions:**
1. Verify NVIDIA GPU is installed:
   ```powershell
   nvidia-smi
   ```
2. Install/update CUDA:
   - Download from https://developer.nvidia.com/cuda-downloads
   - Minimum: CUDA 11.8
3. Install cuDNN (for better performance)
4. Reinstall the application with GPU support

---

### Hotkey Errors

#### "Hotkey Registration Failed"

**Symptoms:**
- Hotkey doesn't work
- Error about hotkey conflict
- Another app using the same hotkey

**Solutions:**
1. Change the hotkey in settings:
   - Try less common combinations (e.g., Ctrl+Alt+R)
   - Avoid media keys that other apps use
2. Close conflicting applications
3. Some apps (games, admin apps) block hotkey registration
4. Run as Administrator if needed

**Common Conflicts:**
- Screen recorders (OBS, Fraps)
- Game overlays (Steam, Discord)
- Hotkey utilities (AutoHotkey, PowerToys)

**Related:** `error_handling.py:HotkeyConflictError`, `hotkey_manager.py`

---

### Clipboard Errors

#### "Clipboard Access Denied"

**Symptoms:**
- Text is not pasted
- Error about clipboard access
- Character-by-character typing fallback activates

**Solutions:**
1. Check clipboard permissions in system settings
2. Some secure apps block clipboard access (password managers)
3. The app automatically falls back to typing mode
4. Verify `pyperclip` is installed (pip installs only):
   ```powershell
   uv pip install pyperclip
   ```

**Typing Fallback:**
When clipboard fails, the app types character-by-character. Note:
- Works best with ASCII text
- May not work with Unicode/emojis
- Requires the target window to be focused

**Related:** `error_handling.py:ClipboardAccessError`, `typing_util.py`

---

### Settings Errors

#### "Settings File Corrupted"

**Symptoms:**
- Application fails to start
- Settings reset to defaults
- Error about invalid JSON

**Solutions:**
1. Automatic recovery:
   - A backup is created automatically
   - Default settings are used
   - Backup location is shown in error message
2. Restore from backup manually:
   ```powershell
   # Check backup location
   dir "%APPDATA%\faster_whisper_hotkey\backups\"
   ```
3. Reset all settings:
   ```powershell
   rmdir /s "%APPDATA%\faster_whisper_hotkey"
   ```

**Automatic Backup:**
The app keeps 5 most recent settings backups.

**Related:** `error_handling.py:SettingsCorruptedError`, `settings.py:validate_settings`

---

#### "Settings Not Persisting"

**Symptoms:**
- Changes are lost after restart
- Settings revert to defaults

**Solutions:**
1. Check write permissions:
   ```powershell
   icacls "%APPDATA%\faster_whisper_hotkey"
   ```
2. Ensure disk is not full
3. Check if file is synced by cloud storage (OneDrive, etc.)
4. Run as Administrator once to initialize

---

## Performance Issues

### Slow Transcription

**Symptoms:**
- Long delay after recording stops
- Transcription takes 10+ seconds

**Diagnosis:**
1. Check which device is being used (Settings → Device)
2. Check model size (larger models = slower)
3. Check CPU/GPU usage in Task Manager

**Solutions:**
1. Use GPU acceleration if available
2. Use a smaller model
3. Reduce recording length
4. Close other applications

**Performance Comparison:**
| Model | CPU (Intel i7) | GPU (RTX 3060) |
|-------|----------------|----------------|
| tiny  | ~2x real-time  | ~0.3x real-time |
| base  | ~4x real-time  | ~0.5x real-time |
| small | ~6x real-time  | ~0.7x real-time |
| medium| ~10x real-time | ~1.2x real-time |
| large | ~20x real-time | ~2x real-time |

---

### High Memory Usage

**Symptoms:**
- Application uses 1-2 GB RAM
- System slows down

**Solutions:**
1. Use a smaller model
2. Enable "Unload model when idle" in settings
3. Close the application when not in use
4. Reduce history max items in settings

**Memory Usage by Model:**
| Model | RAM Required (CPU) | VRAM Required (GPU) |
|-------|-------------------|-------------------|
| tiny  | ~500 MB          | ~1 GB            |
| base  | ~1 GB            | ~1 GB            |
| small | ~2 GB            | ~2 GB            |
| medium| ~4 GB           | ~4 GB            |
| large | ~8 GB            | ~6 GB            |

---

### Application Won't Start

**Symptoms:**
- No window appears
- Crash on startup
- Event Viewer error

**Diagnosis:**
```powershell
# Check Windows Event Log
Get-EventLog -LogName Application -Source *faster* -Newest 10

# Check for crash dumps
dir "%LOCALAPPDATA%\CrashDumps"
```

**Solutions:**
1. Verify VC++ Redistributable is installed:
   - Download from https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Run as Administrator
3. Check antivirus isn't blocking
4. Try portable version
5. Delete settings and restart:
   ```powershell
   rmdir /s "%APPDATA%\faster_whisper_hotkey"
   ```

---

## Log File Analysis

### Log Locations

- **Installed**: `%APPDATA%\faster_whisper_hotkey\logs\`
- **Portable**: `logs\` next to executable

### Log Format

```
2025-01-23 10:15:30,123 - INFO - [transcriber] Starting transcription
2025-01-23 10:15:35,456 - ERROR - [models] Model load failed: CUDA out of memory
```

### Key Log Messages

| Message | Meaning |
|---------|---------|
| `GPU initialization failed` | GPU not available, using CPU |
| `Fell back to audio device` | Microphone changed |
| `Retry successful after N attempts` | Download recovered |
| `Settings corrupted, using defaults` | Settings file issue |
| `Hotkey registration failed` | Conflicting hotkey |

---

## Diagnostic Script

Run this script to gather diagnostic information:

```powershell
# Save as diagnostics.ps1
$OutputFile = "$env:TEMP\fwh_diagnostics.txt"

"=== Faster-Whisper-Hotkey Diagnostics ===" | Out-File -FilePath $OutputFile
"Generated: $(Get-Date)" | Out-File -FilePath $OutputFile -Append

"`n=== System Information ===" | Out-File -FilePath $OutputFile -Append
Get-ComputerInfo | Select-Object OsName, OsVersion, WindowsVersion, CsName, OsHardwareAbstractionLayer | Format-List | Out-File -FilePath $OutputFile -Append

"`n=== GPU Information ===" | Out-File -FilePath $OutputFile -Append
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi | Out-File -FilePath $OutputFile -Append
} else {
    "NVIDIA driver not detected" | Out-File -FilePath $OutputFile -Append
}

"`n=== Audio Devices ===" | Out-File -FilePath $OutputFile -Append
Get-PnpDevice -Class Audio | Where-Object {$_.Status -eq "OK"} | Format-Table Name, Status | Out-File -FilePath $OutputFile -Append

"`n=== Application Files ===" | Out-File -FilePath $OutputFile -Append
if (Test-Path "$env:APPDATA\faster_whisper_hotkey") {
    Get-ChildItem "$env:APPDATA\faster_whisper_hotkey" -Recurse | Select-Object FullName, Length, LastWriteTime | Format-Table | Out-File -FilePath $OutputFile -Append
} else {
    "Settings folder not found" | Out-File -FilePath $OutputFile -Append
}

"`n=== Recent Errors ===" | Out-File -FilePath $OutputFile -Append
Get-EventLog -LogName Application -Source *faster* -Newest 10 -ErrorAction SilentlyContinue | Format-Table TimeGenerated, EntryType, Message | Out-File -FilePath $OutputFile -Append

notepad $OutputFile
```

---

## Getting Help

### Before Requesting Help

1. Check [[known-issues]] for known problems
2. Try the solutions above
3. Collect diagnostic information:
   - Error messages
   - Log files
   - System information
   - Steps to reproduce

### How to Report Bugs

1. **Search existing issues** at https://github.com/blakkd/faster-whisper-hotkey/issues
2. **Create a new issue** with:
   - Clear title describing the problem
   - Steps to reproduce
   - Expected behavior vs actual behavior
   - Error messages or logs
   - System information:
     ```powershell
     systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
     wmic path win32_VideoController get name
     ```
3. **Attach diagnostics** if possible

### Community Resources

- **GitHub Issues**: https://github.com/blakkd/faster-whisper-hotkey/issues
- **Discussions**: https://github.com/blakkd/faster-whisper-hotkey/discussions

---

## Related Documentation

- [[installation]] - Installation and setup
- [[known-issues]] - Known bugs and limitations
- [[TESTING]] - Testing procedures
- [[PORTABLE_MODE]] - Portable mode details
