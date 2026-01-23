"""
Flet GUI views.

This package contains modular UI components (views) for the Flet application.
Each view is a reusable component that can be integrated into the main app.
"""

from .transcription_panel import TranscriptionPanel
from .settings_panel import SettingsPanel
from .modern_settings_panel import ModernSettingsPanel
from .history_panel import HistoryPanel

__all__ = [
    "TranscriptionPanel",
    "SettingsPanel",
    "ModernSettingsPanel",
    "HistoryPanel",
]
