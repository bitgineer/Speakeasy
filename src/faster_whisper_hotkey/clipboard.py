"""
Clipboard operations for faster-whisper-hotkey.

This module provides clipboard management functionality for copying transcribed
text to the system clipboard. It handles backup and restore of clipboard contents
to preserve user data during the transcription process.

Functions
---------
backup_clipboard
    Save the current clipboard content.

set_clipboard
    Copy text to the system clipboard.

restore_clipboard
    Restore previously saved clipboard content.

Notes
-----
If pyperclip is not available, the module falls back to typing each character
individually, which may fail for some special characters in certain text fields.
"""

import logging

logger = logging.getLogger(__name__)

try:
    import pyperclip
except Exception:
    pyperclip = None
    logger.error(
        "pyperclip not found - falling back to typing method - uppercase chars/symbols might fail in some text fields"
    )


def backup_clipboard():
    if pyperclip is None:
        logger.warning("pyperclip unavailable - cannot backup clipboard")
        return None
    try:
        return pyperclip.paste()
    except Exception as e:
        logger.debug(f"Could not read clipboard: {e}")
        return None


def set_clipboard(text: str) -> bool:
    if pyperclip is None:
        logger.warning("pyperclip unavailable - cannot set clipboard")
        return False
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        logger.error(f"Could not set clipboard: {e}")
        return False


def restore_clipboard(original_text: str | None):
    if pyperclip is None:
        return
    try:
        if original_text is None:
            return
        pyperclip.copy(original_text)
    except Exception as e:
        logger.debug(f"Could not restore clipboard: {e}")
