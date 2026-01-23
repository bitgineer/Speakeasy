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

ClipboardBackup
    Context manager for automatic clipboard backup and restore.

Notes
-----
If pyperclip is not available, the module falls back to typing each character
individually, which may fail for some special characters in certain text fields.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

logger = logging.getLogger(__name__)

try:
    import pyperclip
except Exception:
    pyperclip = None
    logger.error(
        "pyperclip not found - falling back to typing method - uppercase chars/symbols might fail in some text fields"
    )


def backup_clipboard() -> Optional[str]:
    """
    Save the current clipboard content.

    Returns
    -------
    str or None
        The current clipboard content, or None if backup failed.
        Returns None if clipboard contains non-text content.
    """
    if pyperclip is None:
        logger.warning("pyperclip unavailable - cannot backup clipboard")
        return None
    try:
        content = pyperclip.paste()
        # Validate that we got text content
        if content is None:
            return None
        # Convert to string to handle any non-str types gracefully
        return str(content)
    except (TypeError, AttributeError) as e:
        # Clipboard contains non-text content (image, file, etc.)
        logger.debug(f"Clipboard contains non-text content: {e}")
        return None
    except Exception as e:
        logger.debug(f"Could not read clipboard: {e}")
        return None


def set_clipboard(text: str) -> bool:
    """
    Copy text to the system clipboard.

    Parameters
    ----------
    text
        Text content to copy to clipboard.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if pyperclip is None:
        logger.warning("pyperclip unavailable - cannot set clipboard")
        return False
    try:
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        pyperclip.copy(text)
        return True
    except Exception as e:
        logger.error(f"Could not set clipboard: {e}")
        return False


def restore_clipboard(original_text: Optional[str]) -> bool:
    """
    Restore previously saved clipboard content.

    Parameters
    ----------
    original_text
        The original clipboard content to restore, or None to skip restore.

    Returns
    -------
    bool
        True if restore was attempted (even if failed), False if skipped.
    """
    if pyperclip is None:
        return False
    try:
        if original_text is None:
            return False
        # Ensure we restore as string
        if not isinstance(original_text, str):
            original_text = str(original_text)
        pyperclip.copy(original_text)
        return True
    except Exception as e:
        logger.debug(f"Could not restore clipboard: {e}")
        return False


@contextmanager
def ClipboardBackup(restore_on_error: bool = True, restore_always: bool = False) -> Generator[Optional[str], None, None]:
    """
    Context manager for automatic clipboard backup and restore.

    Automatically backs up the clipboard on entry and restores it on exit.
    Can restore on exception or always restore depending on parameters.

    Parameters
    ----------
    restore_on_error
        Restore clipboard if an exception occurs (default: True).
    restore_always
        Always restore clipboard on exit, regardless of success (default: False).

    Yields
    ------
    str or None
        The backed up clipboard content.

    Examples
    --------
    >>> with ClipboardBackup() as backup:
    ...     set_clipboard("new content")
    ...     # Do work with clipboard
    ... # Clipboard automatically restored

    >>> with ClipboardBackup(restore_always=True):
    ...     set_clipboard("temporary")
    ...     paste_to_active_window()
    ... # Original clipboard always restored
    """
    original = backup_clipboard()
    exception_occurred = False

    try:
        yield original
    except Exception:
        exception_occurred = True
        if restore_on_error or restore_always:
            restore_clipboard(original)
        raise
    finally:
        if not exception_occurred and restore_always:
            restore_clipboard(original)


def safe_set_and_restore(text: str) -> bool:
    """
    Set clipboard content and restore original after a delay.

    This is useful for paste operations where you want to temporarily
    set the clipboard, paste, then restore the original content.

    Parameters
    ----------
    text
        Text to temporarily place in clipboard.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    original = backup_clipboard()
    try:
        if not set_clipboard(text):
            return False
        # Clipboard is now set, caller should do the paste operation
        # We don't automatically restore to allow paste to happen
        return True
    except Exception as e:
        logger.error(f"Error in safe_set_and_restore: {e}")
        # Restore on error
        restore_clipboard(original)
        return False
