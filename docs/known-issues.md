---
type: reference
title: Known Issues and Limitations
created: 2025-01-23
tags:
  - bugs
  - limitations
  - troubleshooting
  - known-issues
related:
  - "[[installation]]"
  - "[[TESTING]]"
  - "[[PORTABLE_MODE]]"
---

# Known Issues and Limitations

This document catalogues known bugs, limitations, and workarounds for faster-whisper-hotkey.

## Priority Classification

- **Critical**: Application crashes or data loss
- **High**: Major feature broken, impacting usability
- **Medium**: Feature partially broken or unreliable
- **Low**: Minor issues or edge cases

---

## Critical Issues

### C1: Model Loading Failures on Windows without VC++ Redistributable

**Status:** Known Issue | **Workaround:** Available

**Description:**
On Windows systems without the Microsoft Visual C++ Redistributable, the application may fail to start or crash when loading models.

**Symptoms:**
- Error message: "MSVCP140.dll is missing" or similar
- Application crashes on startup
- Model loading failures

**Workaround:**
Install the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).

**Affected Components:** `models.py`

---

## High Priority Issues

### H1: Clipboard Fallback Typing Limited to ASCII

**Status:** Known Limitation | **Workaround:** Use clipboard-based paste

**Description:**
When `pyperclip` is unavailable or clipboard operations fail, the application falls back to character-by-character typing using `pynput`. This fallback only works reliably for ASCII characters and may fail for:
- Unicode characters (emojis, non-Latin scripts)
- Special symbols
- Combined characters

**Symptoms:**
- Missing or garbled characters when pasting
- Incorrect characters typed
- Nothing pasted at all

**Location:** `transcriber.py:539-552`

**Workaround:**
Ensure `pyperclip` is installed and clipboard operations are working. The log will show:
```
pyperclip not found - falling back to typing method
```

**Affected Components:** `clipboard.py`, `transcriber.py`

---

### H2: VSCode Terminal Paste Issues

**Status:** Known Limitation | **Workaround:** Manual paste

**Description:**
Auto-paste functionality may not work correctly in VSCode integrated terminals and some other terminal emulators on Windows.

**Symptoms:**
- Text is copied to clipboard but not pasted
- Need to manually press Ctrl+V or Ctrl+Shift+V

**Reason:**
The Windows implementation uses simple Ctrl+V simulation (`paste.py` only implements X11/Wayland terminal detection).

**Location:** `paste.py` (Linux-only terminal detection)

**Workaround:**
Manually paste with Ctrl+V after transcription completes.

**Affected Components:** `paste.py`

---

### H3: ~~Settings Corruption Not Handled Gracefully~~

**Status:** FIXED | **Fixed in:** Phase 6

**Description:**
If the settings JSON file becomes corrupted, the application may not provide clear error messages or recovery options.

**Resolution:**
- Added comprehensive settings validation with automatic correction
- Corrupted files are automatically backed up before recovery
- `SettingsCorruptedError` exception provides backup file location
- Type checking and range validation for all settings
- Automatic default application for missing/invalid values

**Location:** `settings.py:987-1066` (`load_settings` function)

**Affected Components:** `settings.py`

---

## Medium Priority Issues

### M1: No Thread Safety for State Variables

**Status:** Technical Debt | **Impact:** Race conditions possible

**Description:**
Several state variables in `MicrophoneTranscriber` are accessed from multiple threads without synchronization:
- `is_recording`
- `is_transcribing`
- `active_modifiers`
- `transcription_queue`

**Symptoms:**
- Rare race conditions in rapid hotkey presses
- Inconsistent state reporting
- Potential for duplicate transcriptions

**Location:** `transcriber.py:86-150`

**Affected Components:** `transcriber.py`

---

### M2: Audio Buffer Overflow Not Handled

**Status:** Known Issue | **Impact:** Data loss on long recordings

**Description:**
If recording exceeds `max_buffer_length` (10 minutes at 16kHz), audio data is silently truncated without warning.

**Symptoms:**
- Transcription stops at 10 minutes
- No error or warning to user
- Lost audio data

**Location:** `transcriber.py:434-439`

```python
new_index = self.buffer_index + len(audio_data)
if new_index > self.max_buffer_length:
    audio_data = audio_data[: self.max_buffer_length - self.buffer_index]
    new_index = self.max_buffer_length
```

**Workaround:**
Keep recordings under 10 minutes.

**Affected Components:** `transcriber.py`

---

### M3: ~~Model Download No Retry Logic~~

**Status:** FIXED | **Fixed in:** Phase 6

**Description:**
Model downloads from HuggingFace did not implement automatic retry on network failures.

**Resolution:**
- Added exponential backoff retry logic with jitter (default 3 retries)
- Network error detection identifies retryable failures
- User-friendly error messages with suggestions for non-retryable errors
- Progress tracking includes retry count and status ("retrying")
- Error reports generated for failed downloads after all retries

**Location:** `flet_gui/model_download.py:504-688` (_download_worker method)

**Affected Components:** Model download system

---

### M4: Voxtral 30-Second Chunking May Lose Context

**Status:** Known Limitation | **Impact:** Potential text discontinuity

**Description:**
Voxtral model chunks audio at 30-second boundaries. Text spanning chunk boundaries may lose context at boundaries.

**Symptoms:**
- Inconsistent transcription at chunk boundaries
- Different wording for repeated phrases at different positions

**Location:** `models.py:179-210`

**Workaround:**
For critical work, keep recordings under 30 seconds, or use Whisper models which handle longer context.

**Affected Components:** `models.py`

---

### M5: Hotkey Debounce May Miss Valid Presses

**Status:** Known Issue | **Impact:** Occasional missed hotkey

**Description:**
The 100ms debounce after transcription may prevent immediate re-recording if user presses hotkey quickly.

**Symptoms:**
- Hotkey doesn't respond immediately after transcription
- Must wait 100ms before next transcription

**Location:** `transcriber.py:769-771`

```python
if current_time - self.last_transcription_end_time < 0.1:
    return True
```

**Workaround:**
Wait slightly between transcriptions.

**Affected Components:** `transcriber.py`

---

## Low Priority Issues

### L1: Audio Level Callback No Error Recovery

**Status:** Minor Issue | **Impact:** UI may stop updating

**Description:**
If the audio level callback throws an exception, the callback continues but no recovery mechanism exists.

**Location:** `transcriber.py:638-643`

**Affected Components:** `transcriber.py`

---

### L2: Clipboard Restore Commented Out

**Status:** Intentional Design | **Impact:** Clipboard replaced with transcription

**Description:**
The clipboard restore functionality is intentionally disabled (commented out) to keep transcribed text in clipboard.

**Location:** `transcriber.py:556-559`

```python
# Keep transcript in clipboard instead of restoring original
# if original_clip is not None:
#     time.sleep(0.05)
#     restore_clipboard(original_clip)
```

**Note:** This is intentional behavior, not a bug. Users who want the original clipboard restored can uncomment this code.

**Affected Components:** `transcriber.py`

---

### L3: No Unicode Normalization in Text Processing

**Status:** Minor Limitation | **Impact:** Inconsistent unicode handling

**Description:**
Text processor doesn't normalize Unicode characters, which may cause issues with composed/decomposed characters.

**Affected Components:** `text_processor.py`

---

### L4: Global Settings Variables May Be Stale

**Status:** Technical Debt | **Impact:** Potential inconsistency

**Description:**
`settings.py` has legacy global variables that may become stale if settings directory changes after import.

**Location:** `settings.py:165-169`

```python
# Legacy global variables for backward compatibility
conf_dir = os.path.expanduser("~/.config")
settings_dir = get_settings_dir()
SETTINGS_FILE = get_settings_file()
HISTORY_FILE = get_history_file()
```

**Affected Components:** `settings.py`

---

## Platform-Specific Limitations

### Windows

| Issue | Description | Workaround |
|-------|-------------|------------|
| No portable mode detection from exe | Requires `portable.txt` marker | Create `portable.txt` next to exe |
| Paste to terminals | Always uses Ctrl+V | Manually paste with Ctrl+Shift+V |
| No pulseaudio support | Uses system default audio device | Set default device in Windows settings |

### Linux

| Issue | Description | Workaround |
|-------|-------------|------------|
| Requires xdotool/xprop | For terminal detection on X11 | Install via package manager |
| Requires wtype | For paste on Wayland | Install via package manager |
| No portable mode | Settings always in `~/.config` | Use symlink if needed |

---

## Known Feature Limitations

### Model Support

| Model | Limitation |
|-------|------------|
| **Voxtral** | 30-second chunking, requires GPU (CUDA only) |
| **Canary** | Requires source-target language pair |
| **Parakeet** | No language auto-detection |
| **Whisper** | Largest model size (large-v3) requires significant RAM |

### Text Processing

| Feature | Limitation |
|---------|------------|
| Auto-punctuation | English language optimized only |
| Filler word removal | English-only word list |
| Dictionary matching | Fuzzy matching may give false positives |

### Streaming Transcription

| Limitation | Details |
|------------|---------|
| Whisper only | Parakeet, Canary, Voxtral don't support streaming |
| No word timestamps | Only segment-level timestamps available |

---

## Error Handling Gaps

### Unhandled Exception Scenarios

1. **Audio device disconnect during recording** - ~~Automatic device fallback implemented~~
2. **GPU out of memory** - ~~Automatic CPU fallback with user notification~~
3. **Model file corruption** - No verification or recovery
4. **Hotkey already registered** - May fail to register silently

### User-Friendly Error Messages

A new `error_handling.py` module has been added providing:
- **ErrorCategory**: Constants for error types (MODEL_DOWNLOAD, AUDIO_DEVICE, GPU_INIT, etc.)
- **UserFriendlyError**: Base exception class with user-friendly messages
- **ModelDownloadError**: Specific error for model download failures
- **AudioDeviceError**: Specific error for audio device issues
- **GPUInitializationError**: Specific error for GPU failures
- **HotkeyConflictError**: Specific error for hotkey conflicts
- **ClipboardAccessError**: Specific error for clipboard issues

Each error type includes:
- User-friendly title and description
- Actionable suggestions for resolution
- Technical details for diagnostics
- Optional recovery actions

### Error Recovery System

The `ErrorRecovery` class provides:
- **retry_with_backoff**: Automatic retry with exponential backoff
- **gpu_fallback_recovery**: Try GPU, fall back to CPU on failure
- **audio_device_fallback**: Try alternative audio devices

### Error Reporting

The `ErrorReporter` class provides:
- Detailed error reports with system information
- Error history tracking
- Export to JSON and markdown formats
- Automatic recovery attempt logging

### Missing Validation

1. ~~**Settings values**~~ - Range validation now implemented via `validate_settings()`
2. **Model names** - Typos not caught until load time (use `SettingsService.validate_model()`)
3. **Language codes** - Invalid codes passed through to model (use `SettingsService.validate_language()`)

---

## Work in Progress

The following issues are being addressed in Phase 6:

- [x] Thread safety improvements for state variables (completed in earlier task)
- [x] Audio buffer overflow handling with user notification (completed in earlier task)
- [x] Model download retry logic (completed in this task)
- [x] Settings corruption graceful handling (completed in earlier task)
- [x] Input validation for all settings (completed in earlier task)
- [x] GPU to CPU fallback on initialization failure (completed in this task)
- [x] Audio device fallback on failure (completed in this task)
- [x] User-friendly error messages for common errors (completed in this task)
- [x] Error reporting and recovery system (completed in this task)

---

## Reporting New Issues

If you encounter an issue not listed here:

1. Check if it's covered in [[installation]] troubleshooting
2. Search existing [GitHub Issues](https://github.com/blakkd/faster-whisper-hotkey/issues)
3. When reporting, include:
   - Windows version and build
   - Application version
   - Steps to reproduce
   - Error messages or logs
   - Hardware specs (GPU, RAM)

---

## Related Documentation

- [[installation]] - Installation and troubleshooting
- [[TESTING]] - Testing procedures
- [[PORTABLE_MODE]] - Portable mode details
- [[ARCHITECTURE]] - System architecture
