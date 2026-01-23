"""
Application detection module for faster-whisper-hotkey.

This module provides cross-platform application detection based on window class,
window title, and process name. It supports both X11/Wayland on Linux and
Windows platforms.

Classes
-------
AppMatcher
    Base class for matching applications by various patterns.

AppRule
    Represents a rule for matching and configuring per-application settings.

AppDetector
    Detects the currently active application and matches against rules.

Functions
---------
get_active_window_info
    Get information about the currently active window.

Notes
-----
On Linux, uses xdotool/xprop (X11) or swaymsg (Wayland).
On Windows, uses win32gui.
"""

import re
import subprocess
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import platform

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of application matching strategies."""
    WINDOW_CLASS = "window_class"
    WINDOW_TITLE = "window_title"
    PROCESS_NAME = "process_name"
    REGEX_TITLE = "regex_title"
    REGEX_CLASS = "regex_class"


@dataclass
class AppMatcher:
    """Defines how to match an application."""
    match_type: MatchType
    pattern: str
    case_sensitive: bool = False

    def matches(self, window_class: str = "", window_title: str = "", process_name: str = "") -> bool:
        """Check if this matcher matches the given window info."""
        target = ""
        if self.match_type == MatchType.WINDOW_CLASS:
            target = window_class
        elif self.match_type == MatchType.WINDOW_TITLE:
            target = window_title
        elif self.match_type == MatchType.PROCESS_NAME:
            target = process_name
        elif self.match_type == MatchType.REGEX_TITLE:
            target = window_title
        elif self.match_type == MatchType.REGEX_CLASS:
            target = window_class
        else:
            return False

        if not self.case_sensitive:
            target = target.lower()
            pattern = self.pattern.lower()
        else:
            pattern = self.pattern

        if self.match_type in [MatchType.REGEX_TITLE, MatchType.REGEX_CLASS]:
            try:
                return bool(re.search(pattern, target))
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
                return False
        else:
            return pattern in target


@dataclass
class AppRule:
    """Represents a per-application configuration rule."""
    id: str
    name: str
    matchers: List[AppMatcher]
    priority: int = 0  # Higher priority rules are checked first

    # Per-app settings (None means use global default)
    hotkey: Optional[str] = None
    model_type: Optional[str] = None
    model_name: Optional[str] = None
    compute_type: Optional[str] = None
    device: Optional[str] = None
    language: Optional[str] = None

    # Text processing overrides
    text_processing: Optional[Dict[str, Any]] = None

    # Metadata
    enabled: bool = True
    created_at: str = ""
    notes: str = ""

    def matches(self, window_class: str = "", window_title: str = "", process_name: str = "") -> bool:
        """Check if this rule matches the given window info."""
        if not self.enabled:
            return False
        # All matchers must match (AND logic)
        return all(m.matches(window_class, window_title, process_name) for m in self.matchers)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "matchers": [
                {
                    "match_type": m.match_type.value,
                    "pattern": m.pattern,
                    "case_sensitive": m.case_sensitive
                }
                for m in self.matchers
            ],
            "priority": self.priority,
            "hotkey": self.hotkey,
            "model_type": self.model_type,
            "model_name": self.model_name,
            "compute_type": self.compute_type,
            "device": self.device,
            "language": self.language,
            "text_processing": self.text_processing,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppRule":
        """Create from dictionary."""
        matchers = [
            AppMatcher(
                match_type=MatchType(m["match_type"]),
                pattern=m["pattern"],
                case_sensitive=m.get("case_sensitive", False)
            )
            for m in data.get("matchers", [])
        ]
        return cls(
            id=data["id"],
            name=data["name"],
            matchers=matchers,
            priority=data.get("priority", 0),
            hotkey=data.get("hotkey"),
            model_type=data.get("model_type"),
            model_name=data.get("model_name"),
            compute_type=data.get("compute_type"),
            device=data.get("device"),
            language=data.get("language"),
            text_processing=data.get("text_processing"),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", ""),
            notes=data.get("notes", "")
        )


@dataclass
class WindowInfo:
    """Information about the currently active window."""
    window_class: str = ""
    window_title: str = ""
    process_name: str = ""
    app_id: str = ""  # Wayland app_id


class AppDetector:
    """Detects the currently active application."""

    def __init__(self):
        """Initialize the app detector."""
        self.platform = platform.system()
        self._using_wayland = False

        # Detect Wayland on Linux
        if self.platform == "Linux":
            self._detect_wayland()

    def _detect_wayland(self):
        """Detect if running under Wayland."""
        try:
            # Check WAYLAND_DISPLAY environment variable
            import os
            if os.environ.get("WAYLAND_DISPLAY"):
                self._using_wayland = True
                return
        except Exception:
            pass

        # Try swaymsg
        try:
            subprocess.run(
                ["swaymsg", "-t", "get_version"],
                capture_output=True,
                check=True,
                timeout=1
            )
            self._using_wayland = True
        except Exception:
            self._using_wayland = False

    def get_active_window_info(self) -> WindowInfo:
        """Get information about the currently active window.

        Returns:
            WindowInfo object with available window information
        """
        if self.platform == "Linux":
            if self._using_wayland:
                return self._get_active_window_wayland()
            else:
                return self._get_active_window_x11()
        elif self.platform == "Windows":
            return self._get_active_window_windows()
        else:
            logger.warning(f"Unsupported platform: {self.platform}")
            return WindowInfo()

    def _get_active_window_x11(self) -> WindowInfo:
        """Get active window info on X11."""
        info = WindowInfo()
        try:
            # Get window ID
            win_id = subprocess.check_output(
                ["xdotool", "getactivewindow"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            # Get window class
            try:
                xprop_output = subprocess.check_output(
                    ["xprop", "-id", win_id, "WM_CLASS"],
                    stderr=subprocess.DEVNULL
                ).decode()
                classes = re.findall(r'"([^"]+)"', xprop_output)
                if classes:
                    info.window_class = classes[0]
            except Exception:
                pass

            # Get window title
            try:
                title_output = subprocess.check_output(
                    ["xdotool", "getwindowname", win_id],
                    stderr=subprocess.DEVNULL
                ).decode()
                info.window_title = title_output.strip()
            except Exception:
                pass

            # Get window class name (alternative method)
            try:
                class_output = subprocess.check_output(
                    ["xprop", "-id", win_id, "WM_CLASS_NAME"],
                    stderr=subprocess.DEVNULL
                ).decode()
                match = re.search(r'"([^"]+)"', class_output)
                if match and not info.window_class:
                    info.window_class = match.group(1)
            except Exception:
                pass

            logger.debug(f"X11 window info: class={info.window_class}, title={info.window_title}")

        except Exception as e:
            logger.debug(f"X11 window detection failed: {e}")

        return info

    def _get_active_window_wayland(self) -> WindowInfo:
        """Get active window info on Wayland (Sway)."""
        info = WindowInfo()
        try:
            raw = subprocess.check_output(
                ["swaymsg", "-t", "get_tree"],
                stderr=subprocess.DEVNULL
            )
            import json
            tree = json.loads(raw.decode())

            def find_focused(node):
                if node.get("focused"):
                    return node
                for child in node.get("nodes", []):
                    r = find_focused(child)
                    if r:
                        return r
                for child in node.get("floating_nodes", []):
                    r = find_focused(child)
                    if r:
                        return r
                return None

            focused = find_focused(tree)
            if focused:
                info.app_id = focused.get("app_id", "")
                info.window_title = focused.get("name", "")
                # Use app_id as window_class for consistency
                info.window_class = focused.get("app_id", "")

                # Try to get window class from app_id
                if not info.window_class:
                    info.window_class = info.app_id

                logger.debug(f"Wayland window info: app_id={info.app_id}, title={info.window_title}")

        except Exception as e:
            logger.debug(f"Wayland window detection failed: {e}")

        return info

    def _get_active_window_windows(self) -> WindowInfo:
        """Get active window info on Windows."""
        info = WindowInfo()
        try:
            import win32gui
            import win32process

            hwnd = win32gui.GetForegroundWindow()

            # Get window title
            info.window_title = win32gui.GetWindowText(hwnd)

            # Get window class
            info.window_class = win32gui.GetClassName(hwnd)

            # Get process name
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                import psutil
                process = psutil.Process(pid)
                info.process_name = process.name()
            except Exception:
                pass

            logger.debug(f"Windows window info: class={info.window_class}, title={info.window_title}, process={info.process_name}")

        except ImportError:
            logger.warning("win32gui or psutil not available for Windows app detection")
        except Exception as e:
            logger.debug(f"Windows window detection failed: {e}")

        return info


def get_active_window_info() -> WindowInfo:
    """Convenience function to get active window info."""
    detector = AppDetector()
    return detector.get_active_window_info()
