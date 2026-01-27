"""
Clipboard utilities for text handling.

Provides cross-platform clipboard operations with backup/restore functionality.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_clipboard_backup: Optional[str] = None


def backup_clipboard() -> None:
    """Backup current clipboard contents."""
    global _clipboard_backup
    try:
        import pyperclip

        _clipboard_backup = pyperclip.paste()
    except Exception as e:
        logger.debug(f"Failed to backup clipboard: {e}")
        _clipboard_backup = None


def set_clipboard(text: str) -> bool:
    """
    Set clipboard contents.

    Args:
        text: Text to put on clipboard

    Returns:
        True if successful
    """
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception as e:
        logger.error(f"Failed to set clipboard: {e}")
        return False


def get_clipboard() -> Optional[str]:
    """
    Get clipboard contents.

    Returns:
        Clipboard text or None if failed
    """
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception as e:
        logger.error(f"Failed to get clipboard: {e}")
        return None


def restore_clipboard() -> None:
    """Restore clipboard from backup."""
    global _clipboard_backup
    if _clipboard_backup is not None:
        try:
            import pyperclip

            pyperclip.copy(_clipboard_backup)
        except Exception as e:
            logger.debug(f"Failed to restore clipboard: {e}")
    _clipboard_backup = None
