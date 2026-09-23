# Utilities

Utility functions and helpers for SpeakEasy backend.

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
