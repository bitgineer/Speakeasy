"""
Auto-paste functionality for faster-whisper-hotkey Flet GUI.

This module provides intelligent auto-paste functionality that detects the active
window and inserts text using the appropriate method. It handles clipboard backup
and restore to preserve user data, and supports app-specific paste behaviors.

Classes
-------
PasteMethod
    Enum defining available paste methods.

AutoPasteResult
    Result dataclass for auto-paste operations.

AutoPaste
    Main auto-paste service class.

Notes
-----
- On Windows, uses keyboard simulation via pynput
- On Linux, uses existing paste.py module for X11/Wayland
- Clipboard is backed up before paste and restored after
"""

import logging
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Dict, Any

import platform

from ..clipboard import backup_clipboard, set_clipboard, restore_clipboard
from ..app_detector import get_active_window_info, WindowInfo
from ..terminal import (
    TERMINAL_IDENTIFIERS_X11,
    is_terminal_window_x11,
    get_active_window_class_x11,
)
from ..app_rules_manager import get_app_rules_manager
from .app_paste_rules import get_app_paste_rules_manager

logger = logging.getLogger(__name__)


class PasteMethod(Enum):
    """Available paste methods."""
    CLIPBOARD = "clipboard"  # Use Ctrl+V / Ctrl+Shift+V
    TYPING = "typing"  # Character-by-character typing
    DIRECT = "direct"  # Direct clipboard paste (no restore)


@dataclass
class AutoPasteResult:
    """Result of an auto-paste operation."""
    success: bool
    method_used: PasteMethod
    window_info: WindowInfo = field(default_factory=WindowInfo)
    error_message: str = ""
    duration_ms: float = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "method_used": self.method_used.value,
            "window_class": self.window_info.window_class,
            "window_title": self.window_info.window_title,
            "process_name": self.window_info.process_name,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }


class AutoPaste:
    """
    Auto-paste service for intelligent text insertion.

    This service detects the active window and selects the appropriate
    paste method based on the application type and user configuration.

    Features:
    - Automatic clipboard backup and restore
    - App-specific paste method selection
    - Terminal detection for Ctrl+Shift+V
    - Configurable delays for reliability
    - Cross-platform support (Windows/Linux)

    Attributes
    ----------
    default_method
        Default paste method to use when no app-specific rule matches.
    pre_paste_delay
        Delay in seconds after setting clipboard before sending paste shortcut.
    post_paste_delay
        Delay in seconds after paste before restoring clipboard.
    typing_delay
        Delay in seconds between characters when using typing method.
    """

    # Default terminal identifiers (Windows-specific)
    WINDOWS_TERMINAL_CLASSES = [
        "WindowsTerminal",
        "CascadiaConsole",
        "ConsoleWindowClass",
        "PuTTY",
        "Mintty",
        "Terminals",
        "TabbedTerminal",
    ]

    def __init__(
        self,
        default_method: PasteMethod = PasteMethod.CLIPBOARD,
        pre_paste_delay: float = 0.1,
        post_paste_delay: float = 0.3,
        typing_delay: float = 0.01,
    ):
        """
        Initialize the auto-paste service.

        Parameters
        ----------
        default_method
            Default paste method to use.
        pre_paste_delay
            Delay after setting clipboard (seconds).
        post_paste_delay
            Delay after paste before restoring clipboard (seconds).
        typing_delay
            Delay between characters when typing (seconds).
        """
        self.default_method = default_method
        self.pre_paste_delay = pre_paste_delay
        self.post_paste_delay = post_paste_delay
        self.typing_delay = typing_delay
        self.platform = platform.system()

        # Keyboard controller for Windows
        self._keyboard_controller = None
        if self.platform == "Windows":
            try:
                from pynput import keyboard
                self._keyboard_controller = keyboard.Controller()
            except ImportError:
                logger.warning("pynput not available - auto-paste on Windows may be limited")

        # App rules manager for paste-specific rules
        self._rules_manager = get_app_rules_manager()

        # Callback for result notification
        self._on_result: Optional[Callable[[AutoPasteResult], None]] = None

    def set_result_callback(self, callback: Callable[[AutoPasteResult], None]):
        """
        Set callback for paste results.

        Parameters
        ----------
        callback
            Function to call with paste result.
        """
        self._on_result = callback

    def paste(self, text: str, method: Optional[PasteMethod] = None) -> AutoPasteResult:
        """
        Paste text to the active window.

        Parameters
        ----------
        text
            Text to paste.
        method
            Optional paste method override. If None, detects automatically.

        Returns
        -------
        AutoPasteResult
            Result of the paste operation.
        """
        start_time = time.time()

        if not text:
            return AutoPasteResult(
                success=False,
                method_used=PasteMethod.CLIPBOARD,
                error_message="No text provided",
            )

        # Get active window info
        window_info = get_active_window_info()

        # Determine paste method
        if method is None:
            method = self._determine_paste_method(window_info)

        logger.info(
            f"Pasting to {window_info.window_class} ({window_info.window_title}) "
            f"using {method.value} method"
        )

        try:
            success = False

            if method == PasteMethod.TYPING:
                success = self._paste_by_typing(text, window_info)
            elif method == PasteMethod.DIRECT:
                success = self._paste_direct(text, window_info)
            else:  # CLIPBOARD
                success = self._paste_by_clipboard(text, window_info)

            duration_ms = (time.time() - start_time) * 1000

            result = AutoPasteResult(
                success=success,
                method_used=method,
                window_info=window_info,
                duration_ms=duration_ms,
            )

            if self._on_result:
                self._on_result(result)

            return result

        except Exception as e:
            logger.exception(f"Auto-paste failed: {e}")
            duration_ms = (time.time() - start_time) * 1000

            result = AutoPasteResult(
                success=False,
                method_used=method,
                window_info=window_info,
                error_message=str(e),
                duration_ms=duration_ms,
            )

            if self._on_result:
                self._on_result(result)

            return result

    def _determine_paste_method(self, window_info: WindowInfo) -> PasteMethod:
        """
        Determine the appropriate paste method for the active window.

        Parameters
        ----------
        window_info
            Information about the active window.

        Returns
        -------
        PasteMethod
            The appropriate paste method.
        """
        # Check paste-specific rules first
        paste_rules_manager = get_app_paste_rules_manager()
        paste_method = paste_rules_manager.get_paste_method_for_active_window()
        if paste_method != PasteMethod.CLIPBOARD or self.default_method != PasteMethod.CLIPBOARD:
            return paste_method

        # Auto-detect based on window class
        if self.platform == "Windows":
            return self._determine_method_windows(window_info)
        elif self.platform == "Linux":
            return self._determine_method_linux(window_info)
        else:
            return self.default_method

    def _determine_method_windows(self, window_info: WindowInfo) -> PasteMethod:
        """Determine paste method for Windows."""
        window_class = window_info.window_class.lower()
        window_title = window_info.window_title.lower()
        process_name = window_info.process_name.lower()

        # Check for terminals
        for terminal_id in self.WINDOWS_TERMINAL_CLASSES:
            if terminal_id.lower() in window_class or terminal_id.lower() in process_name:
                # Terminals often need typing method
                return PasteMethod.TYPING

        # Check for admin/UAC prompts
        if "uac" in window_title or "consent" in window_class:
            return PasteMethod.TYPING

        # Default to clipboard
        return PasteMethod.CLIPBOARD

    def _determine_method_linux(self, window_info: WindowInfo) -> PasteMethod:
        """Determine paste method for Linux."""
        window_class = window_info.window_class.lower()

        # Check if terminal
        if any(term in window_class for term in TERMINAL_IDENTIFIERS_X11):
            return PasteMethod.CLIPBOARD  # Uses Ctrl+Shift+V

        return PasteMethod.CLIPBOARD

    def _paste_by_clipboard(self, text: str, window_info: WindowInfo) -> bool:
        """
        Paste using clipboard method (Ctrl+V or Ctrl+Shift+V).

        Parameters
        ----------
        text
            Text to paste.
        window_info
            Active window info.

        Returns
        -------
        bool
            True if successful.
        """
        # Backup existing clipboard
        original_clipboard = backup_clipboard()

        try:
            # Set new clipboard content
            if not set_clipboard(text):
                logger.warning("Failed to set clipboard, falling back to typing")
                return self._paste_by_typing(text, window_info)

            # Wait for clipboard to settle
            time.sleep(self.pre_paste_delay)

            # Send appropriate paste shortcut
            if self.platform == "Windows":
                return self._send_paste_windows(window_info)
            elif self.platform == "Linux":
                return self._send_paste_linux(window_info)
            else:
                logger.warning(f"Clipboard paste not supported on {self.platform}")
                return False

        finally:
            # Restore clipboard after a delay
            time.sleep(self.post_paste_delay)
            restore_clipboard(original_clipboard)

    def _paste_direct(self, text: str, window_info: WindowInfo) -> bool:
        """
        Paste directly to clipboard without restore.

        Parameters
        ----------
        text
            Text to paste.
        window_info
            Active window info.

        Returns
        -------
        bool
            True if successful.
        """
        if not set_clipboard(text):
            return False

        time.sleep(self.pre_paste_delay)

        if self.platform == "Windows":
            return self._send_paste_windows(window_info)
        elif self.platform == "Linux":
            return self._send_paste_linux(window_info)

        return False

    def _paste_by_typing(self, text: str, window_info: WindowInfo) -> bool:
        """
        Paste by typing each character individually.

        Parameters
        ----------
        text
            Text to paste.
        window_info
            Active window info.

        Returns
        -------
        bool
            True if successful.
        """
        if not self._keyboard_controller:
            logger.warning("Keyboard controller not available")
            return False

        try:
            # Small delay before typing
            time.sleep(self.pre_paste_delay)

            for char in text:
                self._keyboard_controller.type(char)
                time.sleep(self.typing_delay)

            return True
        except Exception as e:
            logger.error(f"Typing paste failed: {e}")
            return False

    def _send_paste_windows(self, window_info: WindowInfo) -> bool:
        """
        Send paste shortcut on Windows.

        Parameters
        ----------
        window_info
            Active window info.

        Returns
        -------
        bool
            True if successful.
        """
        if not self._keyboard_controller:
            return False

        try:
            window_class = window_info.window_class.lower()
            process_name = window_info.process_name.lower()

            # Check if terminal
            is_terminal = any(
                term.lower() in window_class or term.lower() in process_name
                for term in self.WINDOWS_TERMINAL_CLASSES
            )

            if is_terminal:
                # Ctrl+Shift+V for terminals
                with self._keyboard_controller.pressed(
                    self._keyboard_controller.Key.ctrl_l,
                    self._keyboard_controller.Key.shift
                ):
                    self._keyboard_controller.press("v")
                    self._keyboard_controller.release("v")
            else:
                # Ctrl+V for most apps
                with self._keyboard_controller.pressed(self._keyboard_controller.Key.ctrl_l):
                    self._keyboard_controller.press("v")
                    self._keyboard_controller.release("v")

            time.sleep(0.05)
            return True

        except Exception as e:
            logger.error(f"Windows paste shortcut failed: {e}")
            return False

    def _send_paste_linux(self, window_info: WindowInfo) -> bool:
        """
        Send paste shortcut on Linux (X11/Wayland).

        Parameters
        ----------
        window_info
            Active window info.

        Returns
        -------
        bool
            True if successful.
        """
        try:
            # Import here to avoid issues on non-Linux platforms
            from ..paste import paste_to_active_window
            paste_to_active_window()
            return True
        except Exception as e:
            logger.error(f"Linux paste shortcut failed: {e}")
            return False

    def paste_async(
        self,
        text: str,
        method: Optional[PasteMethod] = None,
        callback: Optional[Callable[[AutoPasteResult], None]] = None,
    ):
        """
        Paste text asynchronously.

        Parameters
        ----------
        text
            Text to paste.
        method
            Optional paste method override.
        callback
            Optional callback for result.
        """
        def _paste_thread():
            result = self.paste(text, method)
            if callback:
                callback(result)

        thread = threading.Thread(target=_paste_thread, daemon=True)
        thread.start()

    def detect_active_app(self) -> Dict[str, str]:
        """
        Detect the active application for debugging/configuration.

        Returns
        -------
        dict
            Dictionary with window_class, window_title, process_name.
        """
        info = get_active_window_info()
        return {
            "window_class": info.window_class,
            "window_title": info.window_title,
            "process_name": info.process_name,
            "platform": self.platform,
        }

    def test_paste_methods(self) -> Dict[str, Any]:
        """
        Test available paste methods on the current platform.

        Returns
        -------
        dict
            Dictionary with test results for each paste method.
        """
        results = {
            "platform": self.platform,
            "methods": {},
        }

        # Test clipboard availability
        try:
            original = backup_clipboard()
            results["methods"]["clipboard_backup"] = original is not None

            if set_clipboard("test"):
                current = backup_clipboard()
                results["methods"]["clipboard_set"] = current == "test"

                restore_clipboard(original)
                results["methods"]["clipboard_restore"] = True
            else:
                results["methods"]["clipboard_set"] = False
                results["methods"]["clipboard_restore"] = False
        except Exception as e:
            results["methods"]["clipboard_backup"] = False
            results["methods"]["clipboard_error"] = str(e)

        # Test keyboard controller
        results["methods"]["keyboard_available"] = self._keyboard_controller is not None

        # Detect current app
        results["active_app"] = self.detect_active_app()

        return results


# Singleton instance
_instance: Optional[AutoPaste] = None


def get_auto_paste() -> AutoPaste:
    """Get singleton instance of the auto-paste service."""
    global _instance
    if _instance is None:
        _instance = AutoPaste()
    return _instance
