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
"""

__version__ = "0.1.0"

from .app_state import AppState
from .transcription_service import TranscriptionService
from .settings_service import SettingsService
from .history_manager import HistoryManager, HistoryItem

__all__ = [
    "__version__",
    "AppState",
    "TranscriptionService",
    "SettingsService",
    "HistoryManager",
    "HistoryItem",
]
