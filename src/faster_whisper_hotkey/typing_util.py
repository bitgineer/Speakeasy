"""
Typing utility for character-by-character text input.

This module provides robust character-by-character typing functionality
as a fallback when clipboard operations fail. It handles special characters,
Unicode, and provides configurable timing for different applications.

Classes
-------
TypingResult
    Result dataclass for typing operations.

SmartTyper
    Main typing service class with configurable delays.

Functions
---------
type_text
    Convenience function to type text with default settings.

Notes
-----
- Uses pynput keyboard controller for cross-platform support
- Handles special characters via shift key combinations
- Supports configurable delays between characters
- Falls back to clipboard for unsupported Unicode characters
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# Import keyboard module for Key enum
try:
    from pynput import keyboard as _keyboard_module
    KEY_MODULE = _keyboard_module
except ImportError:
    KEY_MODULE = None

# Characters that require shift key on US keyboard
SHIFT_CHARS = {
    '~': '`', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0', '_': '-',
    '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'",
    '<': ',', '>': '.', '?': '/',
}

# Uppercase letters also require shift
UPPERCASE_SHIFT = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

# Characters that can be typed directly without shift
DIRECT_CHARS = set(
    'abcdefghijklmnopqrstuvwxyz0123456789`-=[]\\;\',./ '
)


@dataclass
class TypingResult:
    """Result of a typing operation."""
    success: bool
    chars_typed: int = 0
    chars_skipped: int = 0
    fallback_used: bool = False
    error_message: str = ""
    duration_ms: float = 0


class SmartTyper:
    """
    Smart typing utility for character-by-character text input.

    This class provides intelligent text typing with:
    - Automatic shift key handling for special characters
    - Configurable delays for different applications
    - Unicode fallback via clipboard
    - Error recovery

    Attributes
    ----------
    char_delay
        Delay between characters in seconds (default: 0.01).
    pre_delay
        Delay before starting to type (default: 0.05).
    post_delay
        Delay after typing completes (default: 0.05).
    max_unicode_fallback_chars
        Maximum characters to use clipboard fallback for Unicode.
    """

    def __init__(
        self,
        char_delay: float = 0.01,
        pre_delay: float = 0.05,
        post_delay: float = 0.05,
        max_unicode_fallback_chars: int = 100,
    ):
        """
        Initialize the smart typer.

        Parameters
        ----------
        char_delay
            Delay between characters in seconds.
        pre_delay
            Delay before typing starts in seconds.
        post_delay
            Delay after typing completes in seconds.
        max_unicode_fallback_chars
            Max text length for Unicode clipboard fallback.
        """
        self.char_delay = char_delay
        self.pre_delay = pre_delay
        self.post_delay = post_delay
        self.max_unicode_fallback_chars = max_unicode_fallback_chars

        # Import keyboard controller
        try:
            from pynput import keyboard
            self._keyboard = keyboard.Controller()
            self._available = True
        except ImportError:
            self._keyboard = None
            self._available = False
            logger.warning("pynput not available - typing disabled")

    def is_available(self) -> bool:
        """Check if typing functionality is available."""
        return self._available

    def type(self, text: str) -> TypingResult:
        """
        Type text character by character.

        Parameters
        ----------
        text
            Text to type.

        Returns
        -------
        TypingResult
            Result of the typing operation.
        """
        import time as time_module

        start_time = time_module.time()
        result = TypingResult(success=False)

        if not text:
            result.success = True
            return result

        if not self._available:
            result.error_message = "Keyboard controller not available"
            return result

        try:
            # Check for Unicode characters that need clipboard fallback
            unicode_chars = self._get_unicode_chars(text)
            if unicode_chars and len(text) <= self.max_unicode_fallback_chars:
                logger.debug(f"Using clipboard fallback for {len(unicode_chars)} Unicode chars")
                return self._type_via_clipboard(text)

            # Pre-delay
            if self.pre_delay > 0:
                time_module.sleep(self.pre_delay)

            # Type each character
            chars_typed = 0
            chars_skipped = 0

            for char in text:
                if self._type_char(char):
                    chars_typed += 1
                else:
                    chars_skipped += 1

                if self.char_delay > 0:
                    time_module.sleep(self.char_delay)

            # Post-delay
            if self.post_delay > 0:
                time_module.sleep(self.post_delay)

            result.success = chars_typed > 0
            result.chars_typed = chars_typed
            result.chars_skipped = chars_skipped
            result.duration_ms = (time_module.time() - start_time) * 1000

        except Exception as e:
            logger.error(f"Typing failed: {e}")
            result.error_message = str(e)
            result.duration_ms = (time_module.time() - start_time) * 1000

        return result

    def _type_char(self, char: str) -> bool:
        """
        Type a single character with proper shift handling.

        Parameters
        ----------
        char
            Single character to type.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            # Handle newline
            if char == '\n':
                if KEY_MODULE:
                    self._keyboard.press(KEY_MODULE.Key.enter)
                    self._keyboard.release(KEY_MODULE.Key.enter)
                return True
            elif char == '\r':
                # Skip carriage return
                return True
            elif char == '\t':
                if KEY_MODULE:
                    self._keyboard.press(KEY_MODULE.Key.tab)
                    self._keyboard.release(KEY_MODULE.Key.tab)
                return True

            # Check if character requires shift
            needs_shift = char in SHIFT_CHARS or char in UPPERCASE_SHIFT

            # Get the base character (what to press with/without shift)
            if char in SHIFT_CHARS:
                base_char = SHIFT_CHARS[char]
            elif char in UPPERCASE_SHIFT:
                base_char = char.lower()
            else:
                base_char = char

            # Press shift if needed
            if needs_shift and KEY_MODULE:
                self._keyboard.press(KEY_MODULE.Key.shift)

            # Type the character
            self._keyboard.press(base_char)
            self._keyboard.release(base_char)

            # Release shift if needed
            if needs_shift and KEY_MODULE:
                self._keyboard.release(KEY_MODULE.Key.shift)

            return True

        except Exception as e:
            logger.debug(f"Failed to type character '{char}': {e}")
            return False

    def _get_unicode_chars(self, text: str) -> List[str]:
        """
        Get list of Unicode characters that can't be typed directly.

        Parameters
        ----------
        text
            Text to check.

        Returns
        -------
        List[str]
            List of characters that require special handling.
        """
        unicode_chars = []
        for char in text:
            # Skip ASCII characters (including newlines and tabs)
            if ord(char) > 127 and char not in SHIFT_CHARS and char not in UPPERCASE_SHIFT and char not in DIRECT_CHARS:
                # Skip common extended ASCII that might be typeable
                if ord(char) > 255:
                    unicode_chars.append(char)
        return unicode_chars

    def _type_via_clipboard(self, text: str) -> TypingResult:
        """
        Type text using clipboard fallback for Unicode content.

        Parameters
        ----------
        text
            Text to type via clipboard.

        Returns
        -------
        TypingResult
            Result of the clipboard typing operation.
        """
        import time as time_module
        start_time = time_module.time()

        try:
            from .clipboard import set_clipboard
            from .paste import paste_to_active_window

            # Set clipboard
            if not set_clipboard(text):
                return TypingResult(
                    success=False,
                    error_message="Clipboard fallback failed",
                )

            # Wait for clipboard to settle
            time_module.sleep(0.1)

            # Send paste shortcut
            paste_to_active_window()

            return TypingResult(
                success=True,
                chars_typed=len(text),
                fallback_used=True,
                duration_ms=(time_module.time() - start_time) * 1000,
            )

        except Exception as e:
            return TypingResult(
                success=False,
                error_message=f"Clipboard fallback error: {e}",
                duration_ms=(time_module.time() - start_time) * 1000,
            )


# Singleton instance
_instance: Optional[SmartTyper] = None


def get_smart_typer() -> SmartTyper:
    """Get singleton instance of the smart typer."""
    global _instance
    if _instance is None:
        _instance = SmartTyper()
    return _instance


def type_text(text: str, char_delay: float = 0.01) -> TypingResult:
    """
    Type text with default smart typer settings.

    Parameters
    ----------
    text
        Text to type.
    char_delay
        Delay between characters in seconds.

    Returns
    -------
    TypingResult
        Result of the typing operation.
    """
    typer = get_smart_typer()
    if char_delay != 0.01:
        typer.char_delay = char_delay
    return typer.type(text)
