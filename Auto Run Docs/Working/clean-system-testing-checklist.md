---
type: testing
title: Clean System Testing Checklist and Report
created: 2025-01-23
tags:
  - testing
  - windows
  - distribution
  - quality-assurance
related:
  - "[[TESTING.md]]"
  - "[[Phase-05-Windows-Installer-and-Distribution.md]]"
  - "[[release-process.md]]"
---

# Clean System Testing Checklist and Report

This document provides a comprehensive checklist for testing the faster-whisper-hotkey distribution on clean Windows systems. Use this document during testing and fill in the results.

## Overview

**Purpose:** Verify that the Windows installer and portable distribution work correctly on systems without Python or development tools.

**Testing Coverage:**
- Windows 10 (fresh installation)
- Windows 11 (fresh installation)
- CPU-only systems
- NVIDIA GPU systems
- Limited disk space scenarios
- Upgrade scenarios
- Portable version

## Pre-Test Setup

### Required Test Environments

| Environment | Status | Notes |
|-------------|--------|-------|
| Windows 10 VM (clean) | [ ] | Version: 22H2 or later |
| Windows 11 VM (clean) | [ ] | Version: 23H2 or later |
| Windows 10 + NVIDIA GPU | [ ] | CUDA 12.x compatible |
| CPU-only machine | [ ] | No GPU |
| Limited disk space VM | [ ] | < 5 GB free |

### Required Test Files

- [ ] `faster-whisper-hotkey-setup-x.x.x.exe` (NSIS installer)
- [ ] `faster-whisper-hotkey-portable-x.x.x.zip` (portable package)
- [ ] `SHA256SUMS` (checksums file)

### Before Starting

1. [ ] Verify checksums of all test files
2. [ ] Prepare test data (sample audio files)
3. [ ] Have GitHub release notes handy
4. [ ] Create fresh snapshots of VMs before testing

---

## Test Scenario 1: Fresh Windows 10 Installation

### Environment Setup

| Field | Value |
|-------|-------|
| OS Version | Windows 10 [________] |
| Build Number | [________] |
| RAM | [________] |
| CPU | [________] |
| GPU | [________] |
| Free Disk Space (before) | [________] |
| Python Installed | Yes [ ] No [ ] |
| Date Tested | [________] |

### Installation Test

- [ ] **1.1 Installer Launch**
  - [ ] Double-click installer runs without error
  - [ ] UAC prompt appears (if applicable)
  - [ ] Welcome screen displays correctly

- [ ] **1.2 Installation Options**
  - [ ] Can change installation directory
  - [ ] Can toggle desktop shortcut
  - [ ] Can toggle auto-start on boot
  - [ ] Can choose Start Menu folder
  - [ ] License page displays correctly
  - [ ] Disk space check passes

- [ ] **1.3 Installation Process**
  - [ ] Progress bar displays
  - [ ] No error messages during install
  - [ ] Files copied to destination
  - [ ] Shortcuts created
  - [ ] Registry entries created
  - [ ] Finish page appears
  - [ ] "Launch application" checkbox works

- [ ] **1.4 Post-Installation Verification**
  - [ ] Entry exists in "Apps & Features"
  - [ ] Desktop shortcut works (if created)
  - [ ] Start Menu shortcut works
  - [ ] Installation directory contains expected files
  - [ ] Uninstaller exists

### First Run Test

- [ ] **1.5 Initial Launch**
  - [ ] Application launches within 10 seconds
  - [ ] No console window appears
  - [ ] Main window displays correctly
  - [ ] System tray icon appears

- [ ] **1.6 Setup Wizard**
  - [ ] Wizard appears on first run
  - [ ] Hardware detection screen works:
    - [ ] GPU detected (if present)
    - [ ] CPU features detected
    - [ ] Recommended model appropriate
  - [ ] Model selection screen works
  - [ ] Hotkey configuration screen works
  - [ ] Audio device test screen works:
    - [ ] Microphone list populated
    - [ ] Audio level indicator works
    - [ ] Test recording plays back
  - [ ] Analytics opt-in screen works
  - [ ] Can complete wizard successfully
  - [ ] Can skip wizard successfully

- [ ] **1.7 Post-Wizard State**
  - [ ] Settings saved correctly
  - [ ] Configured hotkey works
  - [ ] Selected model downloads
  - [ ] Can record and transcribe

### Functionality Test

- [ ] **1.8 Core Features**
  - [ ] Recording toggle works
  - [ ] Transcription produces output
  - [ ] Copy to clipboard works
  - [ ] History records transcriptions
  - [ ] Settings can be modified
  - [ ] Model can be changed

- [ ] **1.9 System Integration**
  - [ ] Global hotkey works from any app
  - [ ] System tray menu works
  - [ ] Minimize to tray works
  - [ ] Close from tray works
  - [ ] Auto-start works (if enabled)

### Performance Test

- [ ] **1.10 Performance Metrics**
  - [ ] Startup time: _____ seconds
  - [ ] Idle memory: _____ MB
  - [ ] Recording memory: _____ MB
  - [ ] Idle CPU: _____ %
  - [ ] Recording CPU: _____ %

### Uninstall Test

- [ ] **1.11 Uninstallation**
  - [ ] Uninstall from "Apps & Features" works
  - [ ] Prompt about user data appears
  - [ ] All files removed (if data deleted)
  - [ ] Shortcuts removed
  - [ ] Registry entries cleaned
  - [ ] No leftover traces in AppData (if data deleted)

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```
[Add notes about any issues, errors, or observations]
```


---

## Test Scenario 2: Fresh Windows 11 Installation

### Environment Setup

| Field | Value |
|-------|-------|
| OS Version | Windows 11 [________] |
| Build Number | [________] |
| RAM | [________] |
| CPU | [________] |
| GPU | [________] |
| Free Disk Space (before) | [________] |
| Python Installed | Yes [ ] No [ ] |
| Date Tested | [________] |

### Installation Test

- [ ] **2.1 Installer Launch**
  - [ ] Windows 11 compatible installer
  - [ ] No compatibility warnings
  - [ ] Modern UI styling correct

- [ ] **2.2 Installation Process** (same as 1.2-1.4)
  - [ ] All Windows 10 tests pass

### First Run Test

- [ ] **2.3 Windows 11 Specific**
  - [ ] Taskbar integration works
  - [ ] Rounded corners display correctly
  - [ ] No UI scaling issues at 125%, 150%

### Functionality Test

- [ ] **2.4 Core Features** (same as 1.8-1.9)
  - [ ] All Windows 10 tests pass

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 3: CPU-Only System

### Environment Setup

| Field | Value |
|-------|-------|
| GPU | None / Integrated |
| CPU | [________] |
| Date Tested | [________] |

### Installation Test

- [ ] **3.1 Installation**
  - [ ] Installer runs without GPU dependencies
  - [ ] No CUDA-related errors

### Hardware Detection Test

- [ ] **3.2 Hardware Detection**
  - [ ] App detects no NVIDIA GPU
  - [ ] CPU mode is selected
  - [ ] Appropriate compute type set (int8)
  - [ ] Recommended model is small (tiny/base)

### Functionality Test

- [ ] **3.3 CPU Transcription**
  - [ ] Model downloads successfully
  - [ ] Transcription works (slower acceptable)
  - [ ] No "CUDA not available" errors
  - [ ] CPU usage reasonable during transcription

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 4: NVIDIA GPU System

### Environment Setup

| Field | Value |
|-------|-------|
| GPU Model | [________] |
| VRAM | [________] |
| CUDA Version | [________] |
| Driver Version | [________] |
| Date Tested | [________] |

### Installation Test

- [ ] **4.1 Installation**
  - [ ] Installer runs without errors
  - [ ] No CUDA prerequisite warnings

### Hardware Detection Test

- [ ] **4.2 GPU Detection**
  - [ ] GPU detected correctly
  - [ ] VRAM amount detected
  - [ ] CUDA runtime available (bundled)
  - [ ] CUDA mode selected
  - [ ] Appropriate compute type set (float16/int8)

### Functionality Test

- [ ] **4.3 GPU Transcription**
  - [ ] Model downloads successfully
  - [ ] Transcription uses GPU (check GPU usage)
  - [ ] Transcription is faster than CPU
  - [ ] No out-of-memory errors

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 5: Limited Disk Space

### Environment Setup

| Field | Value |
|-------|-------|
| Free Disk Space | [________] |
| Date Tested | [________] |

### Installation Test

- [ ] **5.1 Low Disk Space Handling**
  - [ ] Installer checks disk space
  - [ ] Warning if < 500 MB available
  - [ ] Error if < 300 MB available
  - [ ] Installer stops gracefully

### Model Download Test

- [ ] **5.2 Large Model on Low Space**
  - [ ] Attempting large model download shows warning
  - [ ] Progress bar shows disk space
  - [ ] Graceful error if insufficient space

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 6: Upgrade from Previous Version

### Environment Setup

| Field | Value |
|-------|-------|
| Old Version | [________] |
| New Version | [________] |
| Old Settings Exist | Yes [ ] No [ ] |
| Old Models Exist | Yes [ ] No [ ] |
| Date Tested | [________] |

### Pre-Upgrade

- [ ] **6.1 Old Version State**
  - [ ] Old version installed
  - [ ] Settings configured
  - [ ] Models downloaded
  - [ ] Transcription history exists (if applicable)

### Upgrade Test

- [ ] **6.2 Upgrade Process**
  - [ ] New installer runs
  - [ ] Detects existing installation
  - [ ] Offers to upgrade
  - [ ] Upgrade completes

### Post-Upgrade Verification

- [ ] **6.3 Settings Migration**
  - [ ] All settings preserved
  - [ ] Hotkey configuration preserved
  - [ ] Model selection preserved
  - [ ] Audio device selection preserved

- [ ] **6.4 Data Preservation**
  - [ ] Downloaded models still work
  - [ ] Transcription history preserved
  - [ ] User data intact

- [ ] **6.5 New Features**
  - [ ] New features accessible
  - [ ] Old features still work
  - [ ] No corruption in settings

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 7: Portable Version

### Environment Setup

| Field | Value |
|-------|-------|
| OS Version | [________] |
| Test Directory | [________] |
| Date Tested | [________] |

### Extraction Test

- [ ] **7.1 Package Extraction**
  - [ ] ZIP file extracts without errors
  - [ ] Contains expected files:
    - [ ] `faster-whisper-hotkey.exe`
    - [ ] `START-portable.bat`
    - [ ] `portable.txt`
    - [ ] `PORTABLE_README.md`

### Launch Test

- [ ] **7.2 Portable Launch**
  - [ ] Double-clicking exe launches app
  - [ ] Using START-portable.bat works
  - [ ] No installation required

### Data Storage Test

- [ ] **7.3 Settings Location**
  - [ ] Settings stored in `./settings/`
  - [ ] Models stored in `./models/`
  - [ ] Nothing in AppData
  - [ ] No registry entries

### Portability Test

- [ ] **7.4 Portability**
  - [ ] Can move folder to different location
  - [ ] Settings and models move with folder
  - [ ] App works from new location
  - [ ] Can copy to another computer

### Cleanup Test

- [ ] **7.5 Removal**
  - [ ] Deleting folder removes all traces
  - [ ] No leftover files in system
  - [ ] No registry cleanup needed

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 8: Update System

### Environment Setup

| Field | Value |
|-------|-------|
| Current Version | [________] |
| Newer Version Available | Yes [ ] No [ ] |
| Date Tested | [________] |

### Update Detection Test

- [ ] **8.1 Update Check**
  - [ ] Manual update check works
  - [ ] Update notification appears
  - [ ] Version comparison correct
  - [ ] Release notes display

### Update Download Test

- [ ] **8.2 Download Process**
  - [ ] Download starts in background
  - [ ] Progress indicator works
  - [ ] Can cancel download
  - [ ] Resume after restart

### Update Installation Test

- [ ] **8.3 Install and Restart**
  - [ ] App closes for update
  - [ ] Update applies successfully
  - [ ] App restarts automatically
  - [ ] New version running

### Update Failure Test

- [ ] **8.4 Error Handling**
  - [ ] Network error handled gracefully
  - [ ] Corrupted download detected
  - [ ] Rollback on failure
  - [ ] Manual retry option

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 9: Auto-Update System

### Environment Setup

| Field | Value |
|-------|-------|
| Update Frequency | Daily [ ] Weekly [ ] Manual [ ] |
| Auto-Download | On [ ] Off [ ] |
| Beta Channel | On [ ] Off [ ] |
| Date Tested | [________] |

### Auto-Start Test

- [ ] **9.1 Boot Auto-Start**
  - [ ] Application starts with Windows
  - [ ] Starts minimized (if configured)
  - [ ] System tray icon appears

### Scheduled Update Check

- [ ] **9.2 Scheduled Checks**
  - [ ] Daily check occurs
  - [ ] Weekly check occurs
  - [ ] No check when set to manual

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Test Scenario 10: Error Recovery

### Error Handling Test

- [ ] **10.1 Network Errors**
  - [ ] Model download failure handled
  - [ ] Update check failure handled
  - [ ] Meaningful error messages

- [ ] **10.2 Permission Errors**
  - [ ] App handles read-only settings
  - [ ] Handles unwritable model directory
  - [ ] Clear error messages

- [ ] **10.3 Crashes**
  - [ ] Crash report created
  - [ ] Can restart after crash
  - [ ] Settings not corrupted

**Result:** PASS [ ] FAIL [ ] PARTIAL [ ]

**Notes:**
```


```


---

## Summary Results

| Scenario | Result | Tester | Date |
|----------|--------|--------|------|
| Windows 10 Fresh Install | [ ] | | |
| Windows 11 Fresh Install | [ ] | | |
| CPU-Only System | [ ] | | |
| NVIDIA GPU System | [ ] | | |
| Limited Disk Space | [ ] | | |
| Upgrade from Previous | [ ] | | |
| Portable Version | [ ] | | |
| Update System | [ ] | | |
| Auto-Update System | [ ] | | |
| Error Recovery | [ ] | | |

### Overall Assessment

- [ ] **All scenarios passed**
- [ ] **Critical issues found**
- [ ] **Non-critical issues found**
- [ ] **Ready for release**
- [ ] **Needs fixes before release**

### Critical Issues Found

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| | | | |

### Non-Critical Issues Found

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| | | | |

---

## Test Sign-Off

**Tested By:** __________________________

**Test Dates:** __________________________

**Version Tested:** __________________________

**Overall Recommendation:**
- [ ] APPROVED for release
- [ ] CONDITIONAL approval (see issues)
- [ ] NOT APPROVED (critical issues)

**Signature:** __________________________

**Date:** __________________________

---

## Appendix: Test Data Files

### Sample Audio Files for Testing

| File | Duration | Purpose |
|------|----------|---------|
| short-test.wav | 5 seconds | Basic transcription |
| medium-test.wav | 30 seconds | Normal transcription |
| long-test.wav | 2 minutes | Long transcription |
| multiple-speakers.wav | 1 minute | Speaker detection |
| quiet-audio.wav | 10 seconds | Low volume test |
| loud-audio.wav | 10 seconds | High volume test |
| background-noise.wav | 30 seconds | Noise filtering |

### Test Phrases

For transcription accuracy testing:

1. "The quick brown fox jumps over the lazy dog."
2. "Testing speech recognition accuracy."
3. "This is a test of the emergency broadcast system."
4. "One, two, three, four, five, six, seven, eight, nine, ten."
5. "Hello world, this is faster-whisper-hotkey."

---

## Quick Reference Test Commands

```batch
REM Check executable version
powershell -Command "(Get-Item 'faster-whisper-hotkey.exe').VersionInfo"

REM Run in debug mode
set FWH_DEBUG=1
faster-whisper-hotkey.exe

REM Check for dependencies
dumpbin /DEPENDENTS faster-whisper-hotkey.exe

REM Monitor resource usage
tasklist /V /FI "IMAGENAME eq faster-whisper-hotkey.exe"

REM Check registry entries
reg query HKLM\Software\faster-whisper-hotkey
reg query HKCU\Software\faster-whisper-hotkey
```

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-01-23 | 1.0 | Initial creation | Maestro |
