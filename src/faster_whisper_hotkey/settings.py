"""
Settings persistence and management for faster-whisper-hotkey.

This module handles loading, saving, and managing application settings
and transcription history. Settings are stored as JSON in the user's
config directory.

Classes
-------
Settings
    Dataclass containing all application configuration options.

Functions
---------
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
"""

import os
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

conf_dir = os.path.expanduser("~/.config")
settings_dir = os.path.join(conf_dir, "faster_whisper_hotkey")
os.makedirs(settings_dir, exist_ok=True)
SETTINGS_FILE = os.path.join(settings_dir, "transcriber_settings.json")


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
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to save settings: {e}")


def load_settings() -> Settings | None:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
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
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history: list, max_items: int = 50):
    """Save transcription history to disk."""
    try:
        # Keep only the most recent items
        history = history[-max_items:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to save history: {e}")


def clear_history():
    """Clear all transcription history from disk."""
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            logger.info("History cleared")
    except IOError as e:
        logger.error(f"Failed to clear history: {e}")
