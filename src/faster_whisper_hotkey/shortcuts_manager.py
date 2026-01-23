"""
Shortcuts manager for handling multiple keyboard shortcuts.

This module provides a comprehensive system for managing keyboard shortcuts
with support for grouping, conflict detection, and import/export.

Classes
-------
Shortcut
    Represents a single keyboard shortcut with ID, name, hotkey, and metadata.

ShortcutConflictError
    Exception raised when a shortcut conflict is detected.

ShortcutsManager
    Main class for managing keyboard shortcuts with persistence and validation.

Functions
---------
get_shortcuts_manager
    Get the global shortcuts manager instance.

parse_hotkey
    Parse a hotkey string into modifiers and main key.

hotkey_matches
    Check if two hotkey strings represent the same key combination.

Notes
-----
Shortcuts are organized into groups: recording, playback, navigation,
history, and application. Configuration is persisted to JSON.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Lazy import of pynput to avoid issues in headless environments
# It's only needed for the keyboard listener in the GUI components
try:
    from pynput import keyboard
except ImportError:
    keyboard = None

from .settings import settings_dir

logger = logging.getLogger(__name__)

# Path to shortcuts configuration file
SHORTCUTS_FILE = os.path.join(settings_dir, "shortcuts_config.json")

# Default shortcut groups
DEFAULT_SHORTCUTS = {
    "recording": [
        {
            "id": "record_toggle",
            "name": "Toggle Recording",
            "hotkey": "pause",
            "description": "Start or stop recording",
            "enabled": True,
        },
        {
            "id": "record_start",
            "name": "Start Recording",
            "hotkey": "",
            "description": "Start recording immediately",
            "enabled": False,
        },
        {
            "id": "record_stop",
            "name": "Stop Recording",
            "hotkey": "",
            "description": "Stop recording and transcribe",
            "enabled": False,
        }
    ],
    "playback": [
        {
            "id": "play_pause",
            "name": "Play/Pause",
            "hotkey": "",
            "description": "Play or pause playback",
            "enabled": False,
        }
    ],
    "navigation": [
        {
            "id": "seek_forward",
            "name": "Seek Forward",
            "hotkey": "",
            "description": "Seek forward in audio",
            "enabled": False,
        },
        {
            "id": "seek_backward",
            "name": "Seek Backward",
            "hotkey": "",
            "description": "Seek backward in audio",
            "enabled": False,
        }
    ],
    "history": [
        {
            "id": "copy_last",
            "name": "Copy Last Transcription",
            "hotkey": "ctrl+shift+c",
            "description": "Copy the last transcription to clipboard",
            "enabled": True,
        },
        {
            "id": "show_history",
            "name": "Show History",
            "hotkey": "ctrl+h",
            "description": "Show the history panel",
            "enabled": True,
        },
        {
            "id": "clear_history",
            "name": "Clear History",
            "hotkey": "",
            "description": "Clear all transcription history",
            "enabled": False,
        }
    ],
    "application": [
        {
            "id": "toggle_app",
            "name": "Toggle Application",
            "hotkey": "",
            "description": "Toggle the application on/off",
            "enabled": False,
        },
        {
            "id": "show_settings",
            "name": "Show Settings",
            "hotkey": "ctrl+,",
            "description": "Open the settings window",
            "enabled": True,
        },
        {
            "id": "show_shortcuts",
            "name": "Show Shortcuts",
            "hotkey": "ctrl+k",
            "description": "Open the shortcuts manager",
            "enabled": True,
        },
        {
            "id": "toggle_privacy",
            "name": "Toggle Privacy Mode",
            "hotkey": "ctrl+shift+p",
            "description": "Toggle privacy mode on/off",
            "enabled": False,
        },
        {
            "id": "exit_app",
            "name": "Exit Application",
            "hotkey": "ctrl+q",
            "description": "Exit the application",
            "enabled": False,
        }
    ],
    "text_processing": [
        {
            "id": "show_dictionary",
            "name": "Show Dictionary",
            "hotkey": "ctrl+d",
            "description": "Open the dictionary manager",
            "enabled": False,
        },
        {
            "id": "show_snippets",
            "name": "Show Snippets",
            "hotkey": "ctrl+shift+s",
            "description": "Open the snippets manager",
            "enabled": False,
        },
        {
            "id": "show_text_processing",
            "name": "Show Text Processing",
            "hotkey": "",
            "description": "Open text processing settings",
            "enabled": False,
        }
    ]
}

# Group display names
GROUP_NAMES = {
    "recording": "Recording Controls",
    "playback": "Playback Controls",
    "navigation": "Navigation",
    "history": "History Management",
    "application": "Application Control",
    "text_processing": "Text Processing",
}


@dataclass
class Shortcut:
    """Represents a single keyboard shortcut."""

    id: str
    name: str
    hotkey: str
    description: str
    enabled: bool = True
    group: str = ""


class ShortcutConflictError(Exception):
    """Raised when a shortcut conflict is detected."""

    def __init__(self, shortcut_id: str, conflicting_with: str):
        self.shortcut_id = shortcut_id
        self.conflicting_with = conflicting_with
        super().__init__(
            f"Shortcut '{shortcut_id}' conflicts with '{conflicting_with}'"
        )


class ShortcutsManager:
    """Manages keyboard shortcuts with conflict detection and persistence."""

    def __init__(self):
        self.shortcuts: Dict[str, Shortcut] = {}
        self.groups: Dict[str, List[str]] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.hotkey_to_id: Dict[str, str] = {}
        # Type as List[Any] since pynput may not be available
        self.listeners: List[Any] = []
        self._listener_running = False

        self.load()

    def load(self) -> None:
        """Load shortcuts from the configuration file."""
        try:
            with open(SHORTCUTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._load_from_dict(data)
        except FileNotFoundError:
            logger.info("No shortcuts config found, using defaults")
            self._load_defaults()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse shortcuts config: {e}")
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default shortcuts."""
        self._load_from_dict(DEFAULT_SHORTCUTS)

    def _load_from_dict(self, data: Dict[str, List[Dict]]) -> None:
        """Load shortcuts from a dictionary structure."""
        self.shortcuts.clear()
        self.groups.clear()
        self.hotkey_to_id.clear()

        for group_name, group_shortcuts in data.items():
            self.groups[group_name] = []
            for shortcut_data in group_shortcuts:
                shortcut = Shortcut(
                    id=shortcut_data["id"],
                    name=shortcut_data["name"],
                    hotkey=shortcut_data.get("hotkey", ""),
                    description=shortcut_data.get("description", ""),
                    enabled=shortcut_data.get("enabled", True),
                    group=group_name,
                )
                self.shortcuts[shortcut.id] = shortcut
                self.groups[group_name].append(shortcut.id)
                if shortcut.hotkey and shortcut.enabled:
                    self.hotkey_to_id[shortcut.hotkey.lower()] = shortcut.id

    def save(self) -> None:
        """Save shortcuts to the configuration file."""
        data = {}
        for group_name, shortcut_ids in self.groups.items():
            data[group_name] = []
            for shortcut_id in shortcut_ids:
                if shortcut_id in self.shortcuts:
                    shortcut = self.shortcuts[shortcut_id]
                    data[group_name].append({
                        "id": shortcut.id,
                        "name": shortcut.name,
                        "hotkey": shortcut.hotkey,
                        "description": shortcut.description,
                        "enabled": shortcut.enabled,
                    })

        try:
            with open(SHORTCUTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save shortcuts: {e}")

    def get(self, shortcut_id: str) -> Optional[Shortcut]:
        """Get a shortcut by ID."""
        return self.shortcuts.get(shortcut_id)

    def get_by_hotkey(self, hotkey: str) -> Optional[Shortcut]:
        """Get a shortcut by its hotkey string."""
        hotkey_lower = hotkey.lower()
        shortcut_id = self.hotkey_to_id.get(hotkey_lower)
        if shortcut_id:
            return self.shortcuts.get(shortcut_id)
        return None

    def get_all(self) -> List[Shortcut]:
        """Get all shortcuts."""
        return list(self.shortcuts.values())

    def get_group(self, group_name: str) -> List[Shortcut]:
        """Get all shortcuts in a group."""
        shortcut_ids = self.groups.get(group_name, [])
        return [self.shortcuts[sid] for sid in shortcut_ids if sid in self.shortcuts]

    def get_group_names(self) -> List[str]:
        """Get all group names."""
        return list(self.groups.keys())

    def set_hotkey(self, shortcut_id: str, hotkey: str) -> Tuple[bool, str]:
        """Set the hotkey for a shortcut.

        Returns:
            Tuple of (success, error_message)
        """
        shortcut = self.shortcuts.get(shortcut_id)
        if not shortcut:
            return False, f"Shortcut '{shortcut_id}' not found"

        # Check for conflicts
        if hotkey:
            conflict = self._find_conflict(shortcut_id, hotkey)
            if conflict:
                return False, f"Conflicts with '{conflict.name}' ({conflict.hotkey})"

        # Remove old hotkey mapping
        if shortcut.hotkey and shortcut.hotkey.lower() in self.hotkey_to_id:
            del self.hotkey_to_id[shortcut.hotkey.lower()]

        # Set new hotkey
        shortcut.hotkey = hotkey
        if hotkey and shortcut.enabled:
            self.hotkey_to_id[hotkey.lower()] = shortcut_id

        return True, ""

    def _find_conflict(self, shortcut_id: str, hotkey: str) -> Optional[Shortcut]:
        """Find if a hotkey conflicts with any existing shortcut."""
        hotkey_lower = hotkey.lower()
        existing_id = self.hotkey_to_id.get(hotkey_lower)
        if existing_id and existing_id != shortcut_id:
            return self.shortcuts.get(existing_id)
        return None

    def detect_all_conflicts(self) -> Dict[str, List[str]]:
        """Detect all shortcut conflicts.

        Returns:
            Dictionary mapping hotkey to list of shortcut IDs using it
        """
        hotkey_users: Dict[str, List[str]] = {}
        conflicts: Dict[str, List[str]] = {}

        for shortcut_id, shortcut in self.shortcuts.items():
            if shortcut.hotkey and shortcut.enabled:
                hotkey_lower = shortcut.hotkey.lower()
                if hotkey_lower not in hotkey_users:
                    hotkey_users[hotkey_lower] = []
                hotkey_users[hotkey_lower].append(shortcut_id)

                if len(hotkey_users[hotkey_lower]) > 1:
                    conflicts[shortcut.hotkey] = hotkey_users[hotkey_lower]

        return conflicts

    def set_enabled(self, shortcut_id: str, enabled: bool) -> None:
        """Enable or disable a shortcut."""
        shortcut = self.shortcuts.get(shortcut_id)
        if not shortcut:
            return

        shortcut.enabled = enabled

        # Update hotkey mapping
        if shortcut.hotkey:
            hotkey_lower = shortcut.hotkey.lower()
            if enabled:
                self.hotkey_to_id[hotkey_lower] = shortcut_id
            elif hotkey_lower in self.hotkey_to_id:
                del self.hotkey_to_id[hotkey_lower]

    def add_shortcut(self, group: str, shortcut: Shortcut) -> Tuple[bool, str]:
        """Add a new shortcut to a group."""
        if shortcut.id in self.shortcuts:
            return False, f"Shortcut ID '{shortcut.id}' already exists"

        # Check for conflicts
        if shortcut.hotkey and shortcut.enabled:
            conflict = self._find_conflict(shortcut.id, shortcut.hotkey)
            if conflict:
                return False, f"Conflicts with '{conflict.name}'"

        self.shortcuts[shortcut.id] = shortcut
        if group not in self.groups:
            self.groups[group] = []
        self.groups[group].append(shortcut.id)

        if shortcut.hotkey and shortcut.enabled:
            self.hotkey_to_id[shortcut.hotkey.lower()] = shortcut.id

        return True, ""

    def remove_shortcut(self, shortcut_id: str) -> bool:
        """Remove a shortcut."""
        shortcut = self.shortcuts.get(shortcut_id)
        if not shortcut:
            return False

        # Remove from hotkey mapping
        if shortcut.hotkey:
            hotkey_lower = shortcut.hotkey.lower()
            if hotkey_lower in self.hotkey_to_id:
                del self.hotkey_to_id[hotkey_lower]

        # Remove from group
        if shortcut.group in self.groups:
            self.groups[shortcut.group] = [
                sid for sid in self.groups[shortcut.group]
                if sid != shortcut_id
            ]

        del self.shortcuts[shortcut_id]
        return True

    def register_callback(self, shortcut_id: str, callback: Callable) -> None:
        """Register a callback for a shortcut."""
        if shortcut_id not in self.callbacks:
            self.callbacks[shortcut_id] = []
        self.callbacks[shortcut_id].append(callback)

    def trigger_shortcut(self, hotkey: str) -> bool:
        """Trigger the callback for a hotkey."""
        hotkey_lower = hotkey.lower()
        shortcut_id = self.hotkey_to_id.get(hotkey_lower)
        if shortcut_id and shortcut_id in self.callbacks:
            for callback in self.callbacks[shortcut_id]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in shortcut callback for {shortcut_id}: {e}")
            return True
        return False

    def export_config(self, path: str) -> Tuple[bool, str]:
        """Export shortcuts configuration to a file.

        Args:
            path: Path to save the export file

        Returns:
            Tuple of (success, message)
        """
        try:
            data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "shortcuts": {}
            }

            for group_name, shortcut_ids in self.groups.items():
                data["shortcuts"][group_name] = []
                for shortcut_id in shortcut_ids:
                    if shortcut_id in self.shortcuts:
                        shortcut = self.shortcuts[shortcut_id]
                        data["shortcuts"][group_name].append({
                            "id": shortcut.id,
                            "name": shortcut.name,
                            "hotkey": shortcut.hotkey,
                            "description": shortcut.description,
                            "enabled": shortcut.enabled,
                        })

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return True, f"Configuration exported to {path}"
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return False, f"Failed to export: {e}"

    def import_config(self, path: str, merge: bool = False) -> Tuple[bool, str]:
        """Import shortcuts configuration from a file.

        Args:
            path: Path to the import file
            merge: If True, merge with existing shortcuts. If False, replace all.

        Returns:
            Tuple of (success, message)
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "shortcuts" not in data:
                return False, "Invalid configuration file format"

            if not merge:
                # Clear existing
                self.shortcuts.clear()
                self.groups.clear()
                self.hotkey_to_id.clear()

            self._load_from_dict(data["shortcuts"])
            self.save()

            return True, "Configuration imported successfully"
        except FileNotFoundError:
            return False, f"File not found: {path}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False, f"Failed to import: {e}"

    def reset_to_defaults(self) -> None:
        """Reset all shortcuts to default values."""
        self._load_defaults()
        self.save()

    def get_hotkey_string(self, hotkey: str) -> str:
        """Format a hotkey string for display."""
        if not hotkey:
            return "Not Set"
        parts = hotkey.lower().split("+")
        # Capitalize for display
        parts = [p.capitalize() if len(p) > 1 else p.upper() for p in parts]
        return "+".join(parts)


# Global shortcuts manager instance
_manager: Optional[ShortcutsManager] = None


def get_shortcuts_manager() -> ShortcutsManager:
    """Get the global shortcuts manager instance."""
    global _manager
    if _manager is None:
        _manager = ShortcutsManager()
    return _manager


def parse_hotkey(hotkey: str) -> Tuple[Set[str], str]:
    """Parse a hotkey string into modifiers and main key.

    Args:
        hotkey: Hotkey string like "ctrl+shift+f1"

    Returns:
        Tuple of (set of modifiers, main key)
    """
    if not hotkey:
        return set(), ""

    parts = hotkey.lower().split("+")
    modifiers = set()
    main_key = ""

    valid_modifiers = {"ctrl", "alt", "shift", "win", "cmd", "meta"}

    for part in parts:
        if part in valid_modifiers:
            modifiers.add(part)
        elif not main_key:
            main_key = part

    return modifiers, main_key


def hotkey_matches(hotkey1: str, hotkey2: str) -> bool:
    """Check if two hotkey strings represent the same key combination."""
    return hotkey1.lower() == hotkey2.lower()
