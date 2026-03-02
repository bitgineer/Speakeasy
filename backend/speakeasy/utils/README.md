# Utilities

Utility functions and helpers for SpeakEasy backend.

## Audio Devices (`audio_devices.py`)
Audio input device enumeration and selection.

Features:
- List all available microphones
- Get device details (name, channels, sample rate)
- Default device detection
- Cross-platform support (Windows, macOS, Linux)

API:
- `list_audio_devices()` - Return all input devices
  ```python
  [
    {
      "id": 0,
      "name": "Built-in Microphone",
      "channels": 1,
      "sample_rate": 44100,
      "is_default": True
    },
    ...
  ]
  ```

## Clipboard (`clipboard.py`)
Text insertion into active window.

Features:
- Cross-platform clipboard access
- Text paste simulation
- Works with global hotkey mode

Platform support:
- Windows: Using `ctypes`
- macOS: Using `AppKit`
- Linux: Using `gtk` or `xclip`

API:
- `insert_text(text)` - Insert text into clipboard and paste
  ```python
  insert_text("Hello, world!")
  ```

## Paste (`paste.py`)
Alternative text paste implementation.

Features:
- Platform-specific implementations
- Fallback strategies
- Error handling for clipboard failures

## Common (`__init__.py`)
Common utilities and helpers:

- Logging configuration
- Path helpers
- String utilities
