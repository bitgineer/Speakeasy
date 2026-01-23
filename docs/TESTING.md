---
type: guide
title: Windows Executable Testing Guide
created: 2024-01-23
tags:
  - testing
  - windows
  - installer
  - release
related:
  - "[[ARCHITECTURE.md]]"
  - "[[flet-architecture.md]]"
---

# Windows Executable Testing Guide

This guide describes how to properly test the `faster-whisper-hotkey` Windows executable before release.

## Overview

Testing on a clean Windows system is critical to ensure the executable works for users who don't have Python or development tools installed. This guide covers:

1. Building the executable
2. Setting up a clean test environment
3. Running automated tests
4. Manual testing checklist
5. Troubleshooting common issues

## Quick Start

```bash
# Build with tests
python scripts/build.py --run-tests

# Test the executable
python scripts/test_executable.py --exe dist/faster-whisper-hotkey.exe
```

## Build System

### Build Options

The `scripts/build.py` script supports several options:

| Option | Description |
|--------|-------------|
| `--run-tests` | Run tests before building |
| `--test-only` | Only run tests, don't build |
| `--clean-only` | Only clean build artifacts |
| `--no-installer` | Skip NSIS installer creation |
| `--no-portable` | Skip portable ZIP creation |
| `--spec flet|qt` | Choose which spec file to build |

### Build Process

1. **Clean**: Removes previous build artifacts
2. **Generate Icon**: Creates the app icon from `installer/create_icon.py`
3. **Build Executable**: Runs PyInstaller with the spec file
4. **Verify**: Checks executable size and validity
5. **Package**: Creates portable ZIP and NSIS installer
6. **Checksums**: Generates SHA256 checksums
7. **Release Notes**: Creates `RELEASE_NOTES.md`

## Clean System Testing

### Why Test on a Clean System?

A "clean" Windows system has:
- No Python installation
- No development tools (Git, compilers, etc.)
- No project-specific dependencies
- Typical user software only

This ensures the executable has **all dependencies bundled** and will work for real users.

### Setting Up a Clean Test Environment

#### Option 1: Virtual Machine (Recommended)

1. Create a new Windows 10 or 11 VM
2. Install only essential software:
   - Web browser (for downloading)
   - 7-Zip (for extracting ZIP files)
3. Copy the built executable to the VM
4. Run tests

#### Option 2: Windows Sandbox

If you have Windows 10/11 Pro or Enterprise:

```powershell
# Enable Windows Sandbox
Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM

# Copy executable to shared folder
# Start Windows Sandbox and map the folder
# Run tests inside the sandbox
```

#### Option 3: Clean Boot

Use a separate user account or Windows To Go on a USB drive.

### Automated Testing

The `scripts/test_executable.py` script runs automated tests:

```bash
# From the project root
python scripts/test_executable.py --exe dist/faster-whisper-hotkey.exe

# Quick tests only (faster)
python scripts/test_executable.py --exe dist/faster-whisper-hotkey.exe --quick
```

#### Test Coverage

| Test | Description |
|------|-------------|
| Executable exists | Verifies file exists and has valid PE header |
| Version info | Checks embedded version information |
| Launch and exit | Launches app and verifies it doesn't crash |
| Settings creation | Verifies settings files are created |
| No missing DLLs | Checks for common DLL dependency errors |
| Portable mode | Tests running with custom app data directory |

### Manual Testing Checklist

#### Installation

- [ ] **Installer runs without errors**
  - Double-click the `.exe` installer
  - Verify no error messages appear
  - Installation completes successfully

- [ ] **Installation options work**
  - Can change installation directory
  - Can toggle desktop shortcut
  - Can toggle auto-start on boot
  - Can choose Start Menu folder

- [ ] **Uninstaller works**
  - Uninstall from "Apps & Features"
  - Verify all files are removed
  - Verify shortcuts are removed
  - Registry entries cleaned up

#### First Run

- [ ] **Application launches**
  - Double-click the executable or desktop shortcut
  - Window appears within 5 seconds
  - No error messages or console windows

- [ ] **Hardware detection**
  - GPU is detected if present (CUDA)
  - CPU features detected
  - Appropriate model recommended

- [ ] **Setup wizard** (if implemented)
  - Can complete setup wizard
  - Settings are saved
  - Can skip wizard if desired

#### Core Functionality

- [ ] **Recording**
  - Press hotkey to start recording
  - Visual indicator shows recording state
  - Press hotkey to stop
  - Transcription appears

- [ ] **Model download**
  - Can select and download a model
  - Progress bar shows download status
  - Model is cached for next run

- [ ] **Settings**
  - Can open settings dialog
  - Changes persist after restart
  - Reset to defaults works

#### System Integration

- [ ] **System tray**
  - Icon appears in system tray
  - Right-click menu works
  - Can minimize to tray
  - Can close from tray

- [ ] **Auto-start**
  - Application starts with Windows (if enabled)
  - Doesn't start with Windows (if disabled)

- [ ] **Hotkeys**
  - Global hotkey works from any application
  - Doesn't interfere with other apps
  - Can customize hotkey

#### Performance

- [ ] **Startup time**
  - Application launches in < 10 seconds
  - System tray appears quickly

- [ ] **Memory usage**
  - Idle memory < 500 MB
  - Recording memory < 2 GB

- [ ] **CPU usage**
  - Idle CPU < 5%
  - Recording CPU varies by model

## Test Scenarios

### Scenario 1: Fresh Install with GPU

1. Start Windows 10/11 with NVIDIA GPU
2. Install the application
3. Launch the application
4. Complete setup wizard
5. Verify GPU is detected
6. Download a model
7. Test recording and transcription

**Expected**: CUDA is detected and used, transcription works

### Scenario 2: CPU-Only System

1. Start Windows 10/11 without GPU
2. Install the application
3. Launch the application
4. Verify CPU is detected
5. Download a small model (tiny or base)
6. Test recording and transcription

**Expected**: CPU mode is used, transcription works (slower)

### Scenario 3: Limited Disk Space

1. Start Windows with < 5 GB free space
2. Install the application
3. Try to download a large model
4. Verify error message about disk space

**Expected**: Graceful error handling, no crash

### Scenario 4: Upgrade from Previous Version

1. Install version N-1 of the application
2. Configure settings
3. Install version N
4. Verify settings are preserved
5. Verify old models still work

**Expected**: Settings and models migrate correctly

## Troubleshooting

### Common Issues

#### "DLL not found" Error

**Cause**: Missing dependency not included in PyInstaller spec

**Solution**:
1. Check the error message for the specific DLL
2. Add to `hiddenimports` in the `.spec` file
3. Rebuild and test again

#### "Application fails to start"

**Cause**: Missing runtime or corrupted build

**Solution**:
1. Verify Visual C++ Redistributable is installed
2. Try rebuilding with `--clean`
3. Check Windows Event Viewer for crash details

#### "Model download fails"

**Cause**: Network issue or missing certificate bundle

**Solution**:
1. Verify internet connectivity
2. Check if `certifi` is included in the build
3. Test with a different network

#### "Settings not saved"

**Cause**: Permissions issue or wrong directory

**Solution**:
1. Run as administrator once to initialize
2. Check `%APPDATA%\faster-whisper-hotkey\`
3. Verify write permissions

### Debug Mode

To enable debug logging, create a batch file:

```batch
@echo off
set FWH_DEBUG=1
set FWH_LOG_FILE=%TEMP%\fwh_debug.log
faster-whisper-hotkey.exe
```

### Collecting Diagnostic Information

```batch
@echo off
REM Create diagnostic report
echo === System Information ===
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"

echo === GPU Information ===
wmic path win32_VideoController get name, driverversion

echo === Application Version ===
powershell -Command "(Get-Item 'faster-whisper-hotkey.exe').VersionInfo"

echo === Event Log Errors ===
powershell -Command "Get-EventLog -LogName Application -Source *faster* -Newest 10"

echo === Files in AppData ===
dir "%APPDATA%\faster-whisper-hotkey"
```

## Continuous Testing

### Pre-Release Checklist

Before any release:

- [ ] Run automated test suite
- [ ] Test on clean Windows 10
- [ ] Test on clean Windows 11
- [ ] Test with NVIDIA GPU
- [ ] Test without GPU (CPU-only)
- [ ] Test installer and uninstaller
- [ ] Test portable version
- [ ] Verify all checksums
- [ ] Test upgrade from previous version

### Automated Testing in CI

See `.github/workflows/build.yml` for automated testing in GitHub Actions.

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [NSIS Documentation](https://nsis.sourceforge.io/)
- [Windows Application Testing](https://docs.microsoft.com/en-us/windows/apps/testing/)
