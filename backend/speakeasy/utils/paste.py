"""
Paste utilities for inserting text into active windows.

Provides cross-platform text insertion via clipboard + key simulation
or direct typing.
"""

import logging
import platform
import subprocess
import time
from typing import Optional

logger = logging.getLogger(__name__)


def _is_wayland() -> bool:
    """Check if running on Wayland."""
    import os

    return os.environ.get("XDG_SESSION_TYPE") == "wayland"


def _is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def _is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def _is_terminal_x11() -> bool:
    """Check if the active window is a terminal (X11)."""
    TERMINAL_IDENTIFIERS = [
        "gnome-terminal",
        "konsole",
        "xfce4-terminal",
        "terminator",
        "tilix",
        "alacritty",
        "kitty",
        "urxvt",
        "xterm",
        "sakura",
        "termite",
        "st",
        "foot",
        "wezterm",
        "contour",
        "qterminal",
        "cool-retro-term",
        "lxterminal",
        "guake",
        "tilda",
        "terminology",
        "hyper",
        "extraterm",
        "deepin-terminal",
        "mate-terminal",
    ]

    try:
        # Get active window ID
        result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return False

        window_id = result.stdout.strip()

        # Get WM_CLASS property
        result = subprocess.run(
            ["xprop", "-id", window_id, "WM_CLASS"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return False

        wm_class = result.stdout.lower()

        for term in TERMINAL_IDENTIFIERS:
            if term in wm_class:
                return True

        return False

    except Exception as e:
        logger.debug(f"Terminal detection failed: {e}")
        return False


def _is_terminal_wayland() -> bool:
    """Check if the active window is a terminal (Wayland/Sway)."""
    TERMINAL_IDENTIFIERS = [
        "gnome-terminal",
        "konsole",
        "alacritty",
        "kitty",
        "foot",
        "wezterm",
        "terminator",
    ]

    try:
        result = subprocess.run(
            ["swaymsg", "-t", "get_tree"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return False

        import json

        tree = json.loads(result.stdout)

        def find_focused(node: dict) -> Optional[dict]:
            if node.get("focused"):
                return node
            for child in node.get("nodes", []) + node.get("floating_nodes", []):
                result = find_focused(child)
                if result:
                    return result
            return None

        focused = find_focused(tree)
        if not focused:
            return False

        app_id = focused.get("app_id", "").lower()
        window_class = focused.get("window_properties", {}).get("class", "").lower()

        for term in TERMINAL_IDENTIFIERS:
            if term in app_id or term in window_class:
                return True

        return False

    except Exception as e:
        logger.debug(f"Wayland terminal detection failed: {e}")
        return False


def _paste_x11(use_shift: bool = False) -> None:
    """Paste using X11 (xdotool not needed, using pynput)."""
    from pynput.keyboard import Controller, Key

    keyboard = Controller()

    if use_shift:
        # Ctrl+Shift+V for terminals
        with keyboard.pressed(Key.ctrl):
            with keyboard.pressed(Key.shift):
                keyboard.press("v")
                keyboard.release("v")
    else:
        # Ctrl+V for normal windows
        with keyboard.pressed(Key.ctrl):
            keyboard.press("v")
            keyboard.release("v")


def _paste_wayland() -> None:
    """Paste using Wayland (wtype)."""
    try:
        # Try wtype for Wayland
        subprocess.run(
            ["wtype", "-M", "ctrl", "v", "-m", "ctrl"],
            timeout=2,
            check=True,
        )
    except FileNotFoundError:
        logger.warning("wtype not found, falling back to pynput")
        _paste_x11(use_shift=False)
    except Exception as e:
        logger.error(f"Wayland paste failed: {e}")


def _paste_windows() -> None:
    """Paste using Windows (pynput)."""
    from pynput.keyboard import Controller, Key

    keyboard = Controller()
    with keyboard.pressed(Key.ctrl):
        keyboard.press("v")
        keyboard.release("v")


def paste_to_active_window() -> None:
    """
    Paste clipboard contents to the active window.

    Handles different platforms and terminal detection.
    """
    # Small delay to ensure clipboard is ready
    time.sleep(0.05)

    if _is_windows():
        _paste_windows()
    elif _is_linux():
        if _is_wayland():
            _paste_wayland()
        else:
            # X11 - check if terminal for Ctrl+Shift+V
            is_terminal = _is_terminal_x11()
            _paste_x11(use_shift=is_terminal)
    else:
        # macOS or other - try generic approach
        from pynput.keyboard import Controller, Key

        keyboard = Controller()
        with keyboard.pressed(Key.cmd):
            keyboard.press("v")
            keyboard.release("v")


def type_text(text: str, interval: float = 0.01) -> None:
    """
    Type text character by character.

    This is a fallback for when clipboard paste doesn't work.

    Args:
        text: Text to type
        interval: Delay between characters in seconds
    """
    from pynput.keyboard import Controller

    keyboard = Controller()

    for char in text:
        keyboard.type(char)
        time.sleep(interval)


def insert_text(
    text: str,
    use_clipboard: bool = True,
    keep_in_clipboard: bool = False,
) -> None:
    """
    Insert text into the active window.

    Args:
        text: Text to insert
        use_clipboard: If True, use clipboard paste. If False, type directly.
        keep_in_clipboard: If True, leave the text in the clipboard after pasting.
    """
    if use_clipboard:
        try:
            from .clipboard import backup_clipboard, restore_clipboard, set_clipboard

            # Backup if we aren't keeping the new text
            if not keep_in_clipboard:
                backup_clipboard()

            if set_clipboard(text):
                paste_to_active_window()
                time.sleep(0.1)  # Wait for paste to complete

                # Restore only if we aren't keeping the new text
                if not keep_in_clipboard:
                    restore_clipboard()
            else:
                # Fallback to typing if clipboard fails
                logger.warning("Clipboard failed, falling back to typing")
                type_text(text)

        except Exception as e:
            logger.error(f"Clipboard paste failed: {e}")
            type_text(text)
    else:
        type_text(text)
