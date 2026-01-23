"""
Flet-based GUI for faster-whisper-hotkey.

This package provides a modern, cross-platform GUI built with Flet
that integrates with the existing transcription engine.

Modules
-------
app
    Main Flet application entry point.

app_state
    Shared UI state management.

transcription_service
    Service layer for transcription operations.

settings_service
    Service layer for settings management.

hotkey_manager
    Hotkey detection and management for Flet.

history_manager
    SQLite-based history storage and management.

auto_paste
    Intelligent auto-paste service for pasting to active windows.

app_paste_rules
    Per-application paste rule management.
"""

__version__ = "0.1.0"

from .app_state import AppState
from .transcription_service import TranscriptionService
from .settings_service import SettingsService
from .history_manager import HistoryManager, HistoryItem
from .auto_paste import AutoPaste, PasteMethod, get_auto_paste
from .app_paste_rules import AppPasteRule, AppPasteRulesManager, get_app_paste_rules_manager

__all__ = [
    "__version__",
    "AppState",
    "TranscriptionService",
    "SettingsService",
    "HistoryManager",
    "HistoryItem",
    "AutoPaste",
    "PasteMethod",
    "get_auto_paste",
    "AppPasteRule",
    "AppPasteRulesManager",
    "get_app_paste_rules_manager",
]
