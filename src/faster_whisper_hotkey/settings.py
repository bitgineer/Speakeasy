"""
Settings persistence and management for faster-whisper-hotkey.

This module handles loading, saving, and managing application settings
and transcription history. Settings are stored as JSON in the user's
config directory, or locally for portable mode.

Classes
-------
Settings
    Dataclass containing all application configuration options.
SettingsValidationError
    Exception raised when settings validation fails.
SettingsBackup
    Context manager for backing up and restoring settings files.

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

validate_settings
    Validate settings values and return cleaned settings with defaults.

load_history
    Load transcription history from disk.

save_history
    Save transcription history to disk with max item limit.

clear_history
    Clear all transcription history from disk.

backup_settings_file
    Create a backup of the settings file.

restore_settings_backup
    Restore a settings file from backup.

Notes
-----
Configuration is stored in ~/.config/faster_whisper_hotkey/ on Linux
and appropriate config directories on other platforms.

In portable mode, settings are stored in a 'settings' subdirectory
next to the executable.

Settings Validation
-------------------
All settings are validated on load with:
- Type checking for all values
- Range validation for numeric values
- Enum validation for choice fields
- Automatic default application for missing values
- Corrupted JSON recovery with backup creation
"""

import os
import sys
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Global variables that will be initialized
_settings_dir = None
_settings_file = None
_history_file = None

# Maximum number of backups to keep
_MAX_SETTINGS_BACKUPS = 5


# ============================================================================
# Exceptions
# ============================================================================

class SettingsValidationError(Exception):
    """Exception raised when settings validation fails.

    Attributes
    ----------
    message
        Error message describing what failed validation.
    field
        The field name that failed validation (if applicable).
    value
        The invalid value that caused the error.
    """

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)

    def __str__(self):
        if self.field:
            return f"Settings validation error for '{self.field}': {self.message}"
        return f"Settings validation error: {self.message}"


class SettingsCorruptedError(Exception):
    """Exception raised when settings file is corrupted.

    This exception is raised when the settings file cannot be parsed
    or contains invalid data that prevents recovery.
    """

    def __init__(self, message: str, backup_path: Optional[str] = None):
        self.message = message
        self.backup_path = backup_path
        super().__init__(self.message)

    def __str__(self):
        msg = self.message
        if self.backup_path:
            msg += f" (Backup saved to: {self.backup_path})"
        return msg


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

    # Update settings
    update_check_frequency: str = "weekly"  # "daily", "weekly", "manually"
    update_include_prereleases: bool = False  # Include beta/preview versions
    update_auto_download: bool = False  # Automatically download updates when available

    # Telemetry settings
    telemetry_enabled: bool = False  # Anonymous usage statistics and crash reporting (opt-in)

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


# ============================================================================
# Settings Backup/Restore
# ============================================================================

def backup_settings_file() -> Optional[str]:
    """Create a backup of the current settings file.

    Returns
    -------
    str or None
        Path to the backup file if successful, None otherwise.
    """
    settings_file = get_settings_file()
    settings_dir = get_settings_dir()

    if not os.path.exists(settings_file):
        return None

    try:
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"transcriber_settings_backup_{timestamp}.json"
        backup_path = os.path.join(settings_dir, backup_filename)

        # Copy the file
        shutil.copy2(settings_file, backup_path)
        logger.info(f"Settings backup created: {backup_path}")

        # Clean up old backups (keep only _MAX_SETTINGS_BACKUPS)
        _cleanup_old_backups()

        return backup_path
    except (IOError, OSError) as e:
        logger.error(f"Failed to create settings backup: {e}")
        return None


def _cleanup_old_backups():
    """Remove old backup files, keeping only the most recent ones."""
    settings_dir = get_settings_dir()

    try:
        # Find all backup files
        backup_files = []
        for filename in os.listdir(settings_dir):
            if filename.startswith("transcriber_settings_backup_") and filename.endswith(".json"):
                filepath = os.path.join(settings_dir, filename)
                backup_files.append((filepath, os.path.getmtime(filepath)))

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)

        # Remove old backups beyond the limit
        for filepath, _ in backup_files[_MAX_SETTINGS_BACKUPS:]:
            try:
                os.remove(filepath)
                logger.debug(f"Removed old backup: {filepath}")
            except OSError as e:
                logger.warning(f"Failed to remove old backup {filepath}: {e}")

    except OSError as e:
        logger.warning(f"Error during backup cleanup: {e}")


def restore_settings_backup(backup_path: str) -> bool:
    """Restore settings from a backup file.

    Parameters
    ----------
    backup_path
        Path to the backup file to restore.

    Returns
    -------
    bool
        True if restore was successful, False otherwise.
    """
    settings_file = get_settings_file()

    if not os.path.exists(backup_path):
        logger.error(f"Backup file not found: {backup_path}")
        return False

    try:
        # Validate the backup file is valid JSON before restoring
        with open(backup_path, "r", encoding="utf-8") as f:
            json.load(f)  # Just to validate

        # Create a backup of current settings before restoring
        if os.path.exists(settings_file):
            backup_settings_file()

        # Copy the backup to the settings file
        shutil.copy2(backup_path, settings_file)
        logger.info(f"Settings restored from: {backup_path}")
        return True

    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to restore settings backup: {e}")
        return False


class SettingsBackup:
    """Context manager for backing up and restoring settings.

    Usage
    -----
    >>> with SettingsBackup() as backup:
    ...     # Modify settings
    ...     save_settings(new_settings)
    ...     # If an exception occurs, settings will be restored
    ...     risky_operation()
    """

    def __init__(self, restore_on_error: bool = True):
        """Initialize the settings backup context manager.

        Parameters
        ----------
        restore_on_error
            If True, restore the backup when an exception occurs.
        """
        self.restore_on_error = restore_on_error
        self.backup_path = None
        self.settings_file = None

    def __enter__(self) -> "SettingsBackup":
        """Create a backup of the current settings."""
        self.settings_file = get_settings_file()
        if os.path.exists(self.settings_file):
            self.backup_path = backup_settings_file()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore backup if an exception occurred and restore_on_error is True."""
        if exc_type is not None and self.restore_on_error and self.backup_path:
            logger.warning(f"Exception occurred, restoring settings from backup")
            restore_settings_backup(self.backup_path)
        return False


# ============================================================================
# Settings Validation
# ============================================================================

# Define valid option sets for validation
_VALID_ACTIVATION_MODES = {"hold", "toggle"}
_VALID_THEME_MODES = {"system", "light", "dark"}
_VALID_UPDATE_FREQUENCIES = {"daily", "weekly", "manually"}
_VALID_CAPITALIZATION_STYLES = {"sentence", "title"}
_VALID_PUNCTUATION_STYLES = {"minimal", "full"}
_VALID_NUMBER_STYLES = {"commas", "words", "both"}
_VALID_TONE_PRESETS = {"neutral", "professional", "casual", "technical", "concise", "creative"}


def _validate_type(value: Any, expected_type: type, field_name: str) -> Any:
    """Validate that a value is of the expected type, converting if possible.

    Parameters
    ----------
    value
        The value to validate.
    expected_type
        The expected type.
    field_name
        Name of the field being validated (for error messages).

    Returns
    -------
    Any
        The validated and possibly converted value.

    Raises
    ------
    SettingsValidationError
        If the value cannot be converted to the expected type.
    """
    if value is None:
        return None

    try:
        # If already the correct type, return as-is
        if isinstance(value, expected_type):
            return value

        # Try to convert to the expected type
        if expected_type == bool:
            # Handle various boolean representations
            if isinstance(value, str):
                if value.lower() in ("true", "1", "yes", "on"):
                    return True
                elif value.lower() in ("false", "0", "no", "off"):
                    return False
            return bool(value)
        elif expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        elif expected_type == str:
            return str(value)
        elif expected_type == dict:
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                # Try to parse JSON string
                return json.loads(value)
            raise ValueError(f"Cannot convert {type(value).__name__} to dict")
        elif expected_type == list:
            if isinstance(value, list):
                return value
            raise ValueError(f"Cannot convert {type(value).__name__} to list")

        return expected_type(value)

    except (ValueError, TypeError, json.JSONDecodeError) as e:
        raise SettingsValidationError(
            f"Invalid type for '{field_name}': expected {expected_type.__name__}, got {type(value).__name__}",
            field=field_name,
            value=value
        )


def _validate_range(value: Any, min_val: Optional[float], max_val: Optional[float],
                    field_name: str) -> Any:
    """Validate that a numeric value is within the specified range.

    Parameters
    ----------
    value
        The value to validate.
    min_val
        Minimum allowed value (inclusive), or None for no minimum.
    max_val
        Maximum allowed value (inclusive), or None for no maximum.
    field_name
        Name of the field being validated.

    Returns
    -------
    Any
        The validated value, clamped to the valid range.

    Raises
    ------
    SettingsValidationError
        If the value cannot be converted to a numeric type.
    """
    try:
        num_value = float(value) if not isinstance(value, (int, float)) else value
    except (ValueError, TypeError):
        raise SettingsValidationError(
            f"Invalid numeric value for '{field_name}': {value}",
            field=field_name,
            value=value
        )

    # Clamp to range
    if min_val is not None and num_value < min_val:
        logger.warning(f"Value for '{field_name}' ({num_value}) below minimum ({min_val}), using minimum")
        return min_val
    if max_val is not None and num_value > max_val:
        logger.warning(f"Value for '{field_name}' ({num_value}) above maximum ({max_val}), using maximum")
        return max_val

    return int(num_value) if isinstance(value, int) or num_value.is_integer() else num_value


def _validate_choice(value: Any, valid_choices: set, field_name: str, default: Any) -> Any:
    """Validate that a value is one of the valid choices.

    Parameters
    ----------
    value
        The value to validate.
    valid_choices
        Set of valid values.
    field_name
        Name of the field being validated.
    default
        Default value to use if validation fails.

    Returns
    -------
    Any
        The validated value, or default if invalid.
    """
    if value is None:
        return default

    str_value = str(value).lower() if not isinstance(value, str) else value

    if str_value in valid_choices:
        return str_value

    # Try case-insensitive match
    for choice in valid_choices:
        if str_value.lower() == choice.lower():
            return choice

    logger.warning(f"Invalid value for '{field_name}': '{value}', using default: '{default}'")
    return default


def validate_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean settings data, applying defaults where needed.

    This function performs comprehensive validation of settings data:
    - Type checking and conversion
    - Range validation for numeric values
    - Choice validation for enum-like fields
    - Default value application for missing fields
    - Nested dictionary validation

    Parameters
    ----------
    data
        Raw settings dictionary loaded from JSON or user input.

    Returns
    -------
    dict
        Validated and cleaned settings dictionary with all required fields.

    Raises
    ------
    SettingsValidationError
        If critical settings are missing or invalid.
    """
    validated = {}
    errors = []

    # Required fields - these must exist and be valid
    required_fields = {
        "device_name": (str, "default_device"),
        "model_type": (str, "whisper"),
        "model_name": (str, "large-v3"),
        "compute_type": (str, "float16"),
        "device": (str, "cpu"),
        "language": (str, "en"),
    }

    # Apply and validate required fields
    for field_name, (field_type, default_value) in required_fields.items():
        if field_name not in data or data[field_name] is None:
            validated[field_name] = default_value
            logger.info(f"Missing required field '{field_name}', using default: '{default_value}'")
        else:
            try:
                validated[field_name] = _validate_type(data[field_name], field_type, field_name)
            except SettingsValidationError as e:
                errors.append(str(e))
                validated[field_name] = default_value

    # Optional fields with defaults
    optional_fields = {
        "hotkey": (str, "pause"),
        "history_hotkey": (str, "ctrl+shift+h"),
        "activation_mode": (_VALID_ACTIVATION_MODES, "hold"),
        "history_max_items": (int, 50, 1, 10000),  # (type, default, min, max)
        "privacy_mode": (bool, False),
        "onboarding_completed": (bool, False),
        "enable_streaming": (bool, False),
        "auto_copy_on_release": (bool, True),
        "confidence_threshold": (float, 0.5, 0.0, 1.0),
        "stream_chunk_duration": (float, 3.0, 0.5, 30.0),
        "theme_mode": (_VALID_THEME_MODES, "system"),
        "history_retention_days": (int, 30, 1, 3650),
        "history_confirm_clear": (bool, True),
        "history_backup_enabled": (bool, False),
        "update_check_frequency": (_VALID_UPDATE_FREQUENCIES, "weekly"),
        "update_include_prereleases": (bool, False),
        "update_auto_download": (bool, False),
        "telemetry_enabled": (bool, False),
    }

    for field_name, spec in optional_fields.items():
        if field_name not in data or data[field_name] is None:
            default = spec[1] if len(spec) > 1 else spec[0]
            validated[field_name] = default
        else:
            value = data[field_name]
            try:
                # Handle choice validation
                if isinstance(spec[0], set):
                    validated[field_name] = _validate_choice(value, spec[0], field_name, spec[1])
                # Handle range validation for numeric fields
                elif len(spec) >= 4:  # Has min/max
                    field_type, default, min_val, max_val = spec[:4]
                    validated[field_name] = _validate_type(value, field_type, field_name)
                    validated[field_name] = _validate_range(validated[field_name], min_val, max_val, field_name)
                # Handle simple type validation
                else:
                    field_type, default = spec[:2]
                    validated[field_name] = _validate_type(value, field_type, field_name)
            except SettingsValidationError as e:
                errors.append(str(e))
                default = spec[1] if len(spec) > 1 else spec[0]
                validated[field_name] = default

    # Validate nested dictionaries
    # Text processing settings
    validated["text_processing"] = _validate_text_processing(data.get("text_processing", {}))

    # Voice command settings
    validated["voice_commands"] = _validate_voice_commands(data.get("voice_commands", {}))

    # Log any validation errors that were corrected
    if errors:
        logger.warning(f"Settings validation corrected {len(errors)} error(s):")
        for error in errors:
            logger.warning(f"  - {error}")

    return validated


def _validate_text_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate text processing settings.

    Parameters
    ----------
    data
        Text processing settings dictionary.

    Returns
    -------
    dict
        Validated text processing settings.
    """
    if not isinstance(data, dict):
        logger.warning("text_processing is not a dict, using defaults")
        return {}

    validated = {}

    # Define text processing fields with their types and defaults
    tp_fields = {
        "remove_filler_words": (bool, True),
        "auto_capitalize": (bool, True),
        "auto_punctuate": (bool, True),
        "format_numbers": (bool, False),
        "expand_acronyms": (bool, False),
        "use_dictionary": (bool, True),
        "filler_aggressiveness": (float, 0.5, 0.0, 1.0),
        "capitalization_style": (_VALID_CAPITALIZATION_STYLES, "sentence"),
        "punctuation_style": (_VALID_PUNCTUATION_STYLES, "minimal"),
        "number_style": (_VALID_NUMBER_STYLES, "commas"),
        "dictionary_fuzzy_matching": (bool, True),
        "tone_preset": (_VALID_TONE_PRESETS, "neutral"),
        "tone_preset_enabled": (bool, False),
    }

    for field_name, spec in tp_fields.items():
        if field_name not in data or data[field_name] is None:
            default = spec[1] if len(spec) > 1 else spec[0]
            validated[field_name] = default
        else:
            value = data[field_name]
            try:
                if isinstance(spec[0], set):
                    validated[field_name] = _validate_choice(value, spec[0], f"text_processing.{field_name}", spec[1])
                elif len(spec) >= 4:
                    field_type, default, min_val, max_val = spec[:4]
                    validated[field_name] = _validate_type(value, field_type, f"text_processing.{field_name}")
                    validated[field_name] = _validate_range(validated[field_name], min_val, max_val, f"text_processing.{field_name}")
                else:
                    field_type, default = spec[:2]
                    validated[field_name] = _validate_type(value, field_type, f"text_processing.{field_name}")
            except SettingsValidationError:
                default = spec[1] if len(spec) > 1 else spec[0]
                validated[field_name] = default

    # Handle list and dict fields
    validated["custom_filler_words"] = _validate_list_field(data.get("custom_filler_words"), "custom_filler_words")
    validated["custom_acronyms"] = _validate_dict_field(data.get("custom_acronyms"), "custom_acronyms")

    return validated


def _validate_voice_commands(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate voice command settings.

    Parameters
    ----------
    data
        Voice command settings dictionary.

    Returns
    -------
    dict
        Validated voice command settings.
    """
    if not isinstance(data, dict):
        logger.warning("voice_commands is not a dict, using defaults")
        return {}

    validated = {}

    vc_fields = {
        "enabled": (bool, True),
        "require_prefix_space": (bool, False),
        "confidence_threshold": (float, 0.5, 0.0, 1.0),
        "key_press_delay": (float, 0.01, 0.0, 1.0),
        "action_delay": (float, 0.05, 0.0, 5.0),
        "case_sensitive": (bool, False),
        "fuzzy_matching": (bool, True),
    }

    for field_name, spec in vc_fields.items():
        if field_name not in data or data[field_name] is None:
            default = spec[1] if len(spec) > 1 else spec[0]
            validated[field_name] = default
        else:
            value = data[field_name]
            try:
                if len(spec) >= 4:
                    field_type, default, min_val, max_val = spec[:4]
                    validated[field_name] = _validate_type(value, field_type, f"voice_commands.{field_name}")
                    validated[field_name] = _validate_range(validated[field_name], min_val, max_val, f"voice_commands.{field_name}")
                else:
                    field_type, default = spec[:2]
                    validated[field_name] = _validate_type(value, field_type, f"voice_commands.{field_name}")
            except SettingsValidationError:
                default = spec[1] if len(spec) > 1 else spec[0]
                validated[field_name] = default

    # Handle command_prefixes list
    validated["command_prefixes"] = _validate_list_field(data.get("command_prefixes", [""]), "command_prefixes")
    if not validated["command_prefixes"]:
        validated["command_prefixes"] = [""]

    return validated


def _validate_list_field(value: Any, field_name: str) -> list:
    """Validate that a value is a list.

    Parameters
    ----------
    value
        The value to validate.
    field_name
        Name of the field being validated.

    Returns
    -------
    list
        Validated list (empty list if invalid).
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    logger.warning(f"Field '{field_name}' is not a list, using empty list")
    return []


def _validate_dict_field(value: Any, field_name: str) -> dict:
    """Validate that a value is a dictionary.

    Parameters
    ----------
    value
        The value to validate.
    field_name
        Name of the field being validated.

    Returns
    -------
    dict
        Validated dictionary (empty dict if invalid).
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    logger.warning(f"Field '{field_name}' is not a dict, using empty dict")
    return {}


# ============================================================================
# Settings Save/Load
# ============================================================================

def save_settings(settings: dict, create_backup: bool = True) -> bool:
    """Save settings dictionary to JSON file with validation and backup.

    Parameters
    ----------
    settings
        Settings dictionary to save.
    create_backup
        If True, create a backup of the existing settings before overwriting.

    Returns
    -------
    bool
        True if save was successful, False otherwise.
    """
    settings_file = get_settings_file()

    try:
        # Validate settings before saving
        validated = validate_settings(settings)

        # Create backup if requested and file exists
        if create_backup and os.path.exists(settings_file):
            backup_settings_file()

        # Ensure directory exists
        settings_dir = get_settings_dir()
        os.makedirs(settings_dir, exist_ok=True)

        # Write to temporary file first (atomic write)
        temp_file = settings_file + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(validated, f, indent=2, ensure_ascii=False)

        # Atomic rename (on Windows, this may not be truly atomic but is still safer)
        if os.path.exists(settings_file):
            os.remove(settings_file)
        os.rename(temp_file, settings_file)

        logger.info(f"Settings saved successfully to {settings_file}")
        return True

    except (IOError, OSError) as e:
        logger.error(f"Failed to save settings: {e}")
        # Clean up temp file if it exists
        temp_file = settings_file + ".tmp"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving settings: {e}")
        return False


def load_settings(raise_on_error: bool = False) -> Optional[Settings]:
    """Load settings from JSON file with validation and error recovery.

    This function loads settings from disk, validates them, and applies
    defaults for any missing or invalid values. If the settings file is
    corrupted, it will attempt to create a backup and recover.

    Parameters
    ----------
    raise_on_error
        If True, raise SettingsCorruptedError when settings cannot be loaded.
        If False, return None on error.

    Returns
    -------
    Settings or None
        The loaded and validated Settings object, or None if loading failed.

    Raises
    ------
    SettingsCorruptedError
        If raise_on_error is True and settings cannot be loaded.
    """
    settings_file = get_settings_file()

    # Check if file exists
    if not os.path.exists(settings_file):
        logger.info(f"Settings file not found at {settings_file}")
        if raise_on_error:
            raise SettingsCorruptedError(f"Settings file not found: {settings_file}")
        return None

    # Try to load and parse the settings file
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    except json.JSONDecodeError as e:
        logger.error(f"Settings file contains invalid JSON: {e}")
        # Create backup of corrupted file
        backup_path = backup_settings_file()
        if backup_path:
            logger.info(f"Corrupted settings backed up to: {backup_path}")
        if raise_on_error:
            raise SettingsCorruptedError(
                f"Settings file contains invalid JSON: {e}",
                backup_path=backup_path
            )
        return None

    except (IOError, OSError) as e:
        logger.error(f"Failed to read settings file: {e}")
        if raise_on_error:
            raise SettingsCorruptedError(f"Failed to read settings file: {e}")
        return None

    # Validate and clean the loaded data
    try:
        validated = validate_settings(data)
        return Settings(**validated)

    except TypeError as e:
        logger.error(f"Settings data has missing required fields: {e}")
        backup_path = backup_settings_file()
        if raise_on_error:
            raise SettingsCorruptedError(
                f"Settings data is invalid: {e}",
                backup_path=backup_path
            )
        return None

    except Exception as e:
        logger.error(f"Unexpected error loading settings: {e}")
        backup_path = backup_settings_file()
        if raise_on_error:
            raise SettingsCorruptedError(
                f"Unexpected error loading settings: {e}",
                backup_path=backup_path
            )
        return None


def create_default_settings(**overrides) -> Settings:
    """Create a Settings object with default values.

    Parameters
    ----------
    **overrides
        Field values to override the defaults.

    Returns
    -------
    Settings
        A Settings object with default values, with any overrides applied.
    """
    defaults = {
        "device_name": "default_device",
        "model_type": "whisper",
        "model_name": "large-v3",
        "compute_type": "float16",
        "device": "cpu",
        "language": "en",
        "hotkey": "pause",
        "history_hotkey": "ctrl+shift+h",
        "activation_mode": "hold",
        "history_max_items": 50,
        "privacy_mode": False,
        "onboarding_completed": False,
        "text_processing": {},
        "enable_streaming": False,
        "auto_copy_on_release": True,
        "confidence_threshold": 0.5,
        "stream_chunk_duration": 3.0,
        "voice_commands": {},
        "theme_mode": "system",
        "history_retention_days": 30,
        "history_confirm_clear": True,
        "history_backup_enabled": False,
        "update_check_frequency": "weekly",
        "update_include_prereleases": False,
        "update_auto_download": False,
        "telemetry_enabled": False,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def load_history(backup_corrupted: bool = True) -> list:
    """Load transcription history from disk with corrupted file handling.

    Parameters
    ----------
    backup_corrupted
        If True, create a backup of corrupted history files before returning empty list.

    Returns
    -------
    list
        List of history items, or empty list if file doesn't exist or is corrupted.
    """
    history_file = get_history_file()

    if not os.path.exists(history_file):
        return []

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

        # Validate that history is a list
        if not isinstance(history, list):
            logger.warning(f"History file contains invalid data type (expected list, got {type(history).__name__})")
            if backup_corrupted:
                _backup_corrupted_history(history_file)
            return []

        return history

    except json.JSONDecodeError as e:
        logger.error(f"History file contains invalid JSON: {e}")
        if backup_corrupted:
            _backup_corrupted_history(history_file)
        return []

    except (IOError, OSError) as e:
        logger.error(f"Failed to read history file: {e}")
        return []


def _backup_corrupted_history(history_file: str) -> Optional[str]:
    """Create a backup of a corrupted history file.

    Parameters
    ----------
    history_file
        Path to the corrupted history file.

    Returns
    -------
    str or None
        Path to the backup file if successful, None otherwise.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        settings_dir = get_settings_dir()
        backup_filename = f"transcription_history_corrupted_{timestamp}.json"
        backup_path = os.path.join(settings_dir, backup_filename)

        shutil.copy2(history_file, backup_path)
        logger.info(f"Corrupted history backed up to: {backup_path}")
        return backup_path
    except (IOError, OSError) as e:
        logger.error(f"Failed to backup corrupted history: {e}")
        return None


def save_history(history: list, max_items: int = 50) -> bool:
    """Save transcription history to disk with validation.

    Parameters
    ----------
    history
        List of history items to save.
    max_items
        Maximum number of items to keep (most recent).

    Returns
    -------
    bool
        True if save was successful, False otherwise.
    """
    # Validate input
    if not isinstance(history, list):
        logger.error(f"Invalid history type: expected list, got {type(history).__name__}")
        return False

    try:
        # Keep only the most recent items
        history = history[-max_items:] if len(history) > max_items else history

        history_file = get_history_file()
        settings_dir = get_settings_dir()
        os.makedirs(settings_dir, exist_ok=True)

        # Write to temporary file first (atomic write)
        temp_file = history_file + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        # Atomic rename
        if os.path.exists(history_file):
            os.remove(history_file)
        os.rename(temp_file, history_file)

        logger.debug(f"History saved ({len(history)} items)")
        return True

    except (IOError, OSError) as e:
        logger.error(f"Failed to save history: {e}")
        # Clean up temp file if it exists
        temp_file = history_file + ".tmp"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        return False


def clear_history() -> bool:
    """Clear all transcription history from disk.

    Returns
    -------
    bool
        True if clear was successful, False otherwise.
    """
    try:
        history_file = get_history_file()
        if os.path.exists(history_file):
            os.remove(history_file)
            logger.info("History cleared")
        return True
    except (IOError, OSError) as e:
        logger.error(f"Failed to clear history: {e}")
        return False
