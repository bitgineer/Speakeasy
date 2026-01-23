"""
faster-whisper-hotkey: Push-to-talk transcription.

Hold the hotkey, Speak, Release ==> And baamm in the currently focused text field!

This package provides real-time audio transcription with hotkey activation.
It supports multiple ASR models (Whisper, Parakeet, Canary, Voxtral) and
provides both CLI and GUI interfaces.

Modules
-------
clipboard
    Clipboard operations for text copying and pasting.

config
    Model and language configuration data.

models
    Model wrapper for loading and running different ASR models.

paste
    Platform-specific paste operations for X11 and Wayland.

terminal
    Terminal window detection for proper paste handling.

transcriber
    Core transcription engine with hotkey support.

settings
    Settings persistence and management.

ui
    Terminal-based UI components using curses.

hotkey_dialog
    GUI dialog for capturing keyboard shortcuts.

history_panel
    GUI for viewing and managing transcription history.

shortcuts_manager
    Keyboard shortcuts management with conflict detection.

shortcuts_panel
    GUI panel for configuring keyboard shortcuts.

onboarding
    Interactive tutorial for first-time users.

cli
    Comprehensive command-line interface.

gui
    System tray GUI application.

voice_command
    Voice command parser and execution framework for editing and control.

text_processor
    Configurable text processing pipeline for transcriptions.

See Also
--------
faster_whisper : Whisper model wrapper
nemo : NVIDIA's NeMo models (Parakeet, Canary)
transformers : Hugging Face transformers (Voxtral)
"""

__version__ = "0.5.0"

# Modern GUI components
from .theme import Theme, ModernStyle, ThemeManager
from .icons import Icon, ModernIcons, IconFactory

# Voice command exports
from .voice_command import (
    VoiceCommand,
    VoiceCommandParser,
    VoiceCommandExecutor,
    VoiceCommandConfig,
    CommandType,
    process_with_commands,
)

__all__ = [
    "__version__",
    # GUI components
    "Theme",
    "ModernStyle",
    "ThemeManager",
    "Icon",
    "ModernIcons",
    "IconFactory",
    # Voice command exports
    "VoiceCommand",
    "VoiceCommandParser",
    "VoiceCommandExecutor",
    "VoiceCommandConfig",
    "CommandType",
    "process_with_commands",
]
