"""
Settings persistence and management for faster-whisper-hotkey.

This module handles loading, saving, and managing application settings
and transcription history. Settings are stored as JSON in the user's
config directory, or locally for portable mode.

Classes
-------
Settings
    Dataclass containing all application configuration options.

Functions
---------
is_portable_mode
    Detect if the application is running in portable mode.

get_settings_dir
    Get the appropriate settings directory for portable or installed mode.

save_settings
    Save settings dictionary to JSON file.

load_settings
    Load settings from JSON file into Settings dataclass.

load_history
    Load transcription history from disk.

save_history
    Save transcription history to disk with max item limit.

clear_history
    Clear all transcription history from disk.

Notes
-----
Configuration is stored in ~/.config/faster_whisper_hotkey/ on Linux
and appropriate config directories on other platforms.

In portable mode, settings are stored in a 'settings' subdirectory
next to the executable.
"""

import os
import sys
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Global variables that will be initialized
_settings_dir = None
_settings_file = None
_history_file = None


def is_portable_mode() -> bool:
    """
    Detect if the application is running in portable mode.

    Portable mode is detected by:
    1. Checking for a 'portable.txt' marker file next to the executable
    2. Checking for a 'settings' directory next to the executable
    3. Checking if the launcher set the PORTABLE_MODE environment variable

    Returns
    -------
    bool
        True if running in portable mode, False otherwise.
    """
    # Check environment variable first (set by portable launcher)
    if os.environ.get('PORTABLE_MODE') == '1':
        return True

    # Check if running as frozen executable
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)

        # Check for portable marker file
        marker_file = os.path.join(exe_dir, 'portable.txt')
        if os.path.exists(marker_file):
            return True

        # Check for existing portable settings directory
        portable_settings = os.path.join(exe_dir, 'settings')
        if os.path.exists(portable_settings):
            return True

    return False


def get_settings_dir() -> str:
    """
    Get the appropriate settings directory based on mode.

    Returns
    -------
    str
        Path to the settings directory.
    """
    global _settings_dir

    if _settings_dir is not None:
        return _settings_dir

    if is_portable_mode():
        # Portable mode: store settings next to executable
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            _settings_dir = os.path.join(exe_dir, 'settings')
        else:
            # Development mode: use local directory
            _settings_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'portable_settings')
            _settings_dir = os.path.abspath(_settings_dir)
    else:
        # Installed mode: use user config directory
        if sys.platform == 'win32':
            conf_dir = os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
        else:
            conf_dir = os.path.expanduser('~/.config')
        _settings_dir = os.path.join(conf_dir, 'faster_whisper_hotkey')

    os.makedirs(_settings_dir, exist_ok=True)
    return _settings_dir


def get_settings_file() -> str:
    """
    Get the settings file path.

    Returns
    -------
    str
        Path to the settings file.
    """
    global _settings_file

    if _settings_file is None:
        settings_dir = get_settings_dir()
        _settings_file = os.path.join(settings_dir, 'transcriber_settings.json')

    return _settings_file


def get_history_file() -> str:
    """
    Get the history file path.

    Returns
    -------
    str
        Path to the history file.
    """
    global _history_file

    if _history_file is None:
        settings_dir = get_settings_dir()
        _history_file = os.path.join(settings_dir, 'transcription_history.json')

    return _history_file


# Legacy global variables for backward compatibility
conf_dir = os.path.expanduser("~/.config")
settings_dir = get_settings_dir()
SETTINGS_FILE = get_settings_file()
HISTORY_FILE = get_history_file()


@dataclass
class TextProcessingSettings:
    """Settings for the text processing pipeline."""
    remove_filler_words: bool = True
    auto_capitalize: bool = True
    auto_punctuate: bool = True
    format_numbers: bool = False
    expand_acronyms: bool = False
    use_dictionary: bool = True  # Enable personal dictionary corrections
    filler_aggressiveness: float = 0.5
    capitalization_style: str = "sentence"  # "sentence" or "title"
    punctuation_style: str = "minimal"  # "minimal" or "full"
    number_style: str = "commas"  # "commas", "words", or "both"
    dictionary_fuzzy_matching: bool = True  # Use fuzzy matching for dictionary
    custom_filler_words: list = None
    custom_acronyms: dict = None
    # Tone style preset settings
    tone_preset: str = "neutral"  # "neutral", "professional", "casual", "technical", "concise", "creative"
    tone_preset_enabled: bool = False  # Enable tone style processing

    def __post_init__(self):
        if self.custom_filler_words is None:
            self.custom_filler_words = []
        if self.custom_acronyms is None:
            self.custom_acronyms = {}


@dataclass
class Settings:
    device_name: str
    model_type: str
    model_name: str
    compute_type: str
    device: str
    language: str
    hotkey: str = "pause"
    history_hotkey: str = "ctrl+shift+h"  # Hotkey for quick history access
    activation_mode: str = "hold"  # "hold" or "toggle"
    history_max_items: int = 50
    privacy_mode: bool = False  # When True, disable history and delete audio immediately
    onboarding_completed: bool = False  # When True, interactive tutorial has been completed
    text_processing: dict = None  # Text processing settings dict

    # Streaming transcription settings
    enable_streaming: bool = False  # Enable real-time streaming transcription preview
    auto_copy_on_release: bool = True  # Auto-copy text to clipboard on hotkey release (streaming mode)
    confidence_threshold: float = 0.5  # Threshold for low-confidence highlighting (0-1)
    stream_chunk_duration: float = 3.0  # Duration of audio chunks for streaming (seconds)

    # Voice command settings
    voice_commands: dict = None  # Voice command settings dict

    # Theme settings
    theme_mode: str = "system"  # "system", "light", or "dark"

    # History settings
    history_retention_days: int = 30  # Auto-delete history older than X days
    history_confirm_clear: bool = True  # Confirm before clearing history
    history_backup_enabled: bool = False  # Auto-backup history before clearing

    def __post_init__(self):
        if self.text_processing is None:
            self.text_processing = {}
        if self.voice_commands is None:
            self.voice_commands = {}

    def get_text_processing_settings(self) -> TextProcessingSettings:
        """Get text processing settings with defaults."""
        return TextProcessingSettings(**self.text_processing)

    def get_voice_command_settings(self) -> dict:
        """Get voice command settings with defaults."""
        return {
            'enabled': self.voice_commands.get('enabled', True),
            'command_prefixes': self.voice_commands.get('command_prefixes', [""]),
            'require_prefix_space': self.voice_commands.get('require_prefix_space', False),
            'confidence_threshold': self.voice_commands.get('confidence_threshold', 0.5),
            'key_press_delay': self.voice_commands.get('key_press_delay', 0.01),
            'action_delay': self.voice_commands.get('action_delay', 0.05),
            'case_sensitive': self.voice_commands.get('case_sensitive', False),
            'fuzzy_matching': self.voice_commands.get('fuzzy_matching', True),
        }


# History file path
HISTORY_FILE = os.path.join(settings_dir, "transcription_history.json")


def save_settings(settings: dict):
    try:
        settings_file = get_settings_file()
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to save settings: {e}")


def load_settings() -> Settings | None:
    try:
        settings_file = get_settings_file()
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("hotkey", "pause")
            data.setdefault("history_hotkey", "ctrl+shift+h")
            data.setdefault("model_type", "whisper")
            data.setdefault("model_name", "large-v3")
            data.setdefault("activation_mode", "hold")
            data.setdefault("history_max_items", 50)
            data.setdefault("privacy_mode", False)
            data.setdefault("onboarding_completed", False)
            data.setdefault("text_processing", {})
            # Streaming settings with defaults
            data.setdefault("enable_streaming", False)
            data.setdefault("auto_copy_on_release", True)
            data.setdefault("confidence_threshold", 0.5)
            data.setdefault("stream_chunk_duration", 3.0)
            # Voice command settings with defaults
            data.setdefault("voice_commands", {})
            # Theme settings with defaults
            data.setdefault("theme_mode", "system")
            # History settings with defaults
            data.setdefault("history_retention_days", 30)
            data.setdefault("history_confirm_clear", True)
            data.setdefault("history_backup_enabled", False)
            return Settings(**data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load settings: {e}")
        return None


def load_history() -> list:
    """Load transcription history from disk."""
    try:
        history_file = get_history_file()
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history: list, max_items: int = 50):
    """Save transcription history to disk."""
    try:
        # Keep only the most recent items
        history = history[-max_items:]
        history_file = get_history_file()
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to save history: {e}")


def clear_history():
    """Clear all transcription history from disk."""
    try:
        history_file = get_history_file()
        if os.path.exists(history_file):
            os.remove(history_file)
            logger.info("History cleared")
    except IOError as e:
        logger.error(f"Failed to clear history: {e}")
