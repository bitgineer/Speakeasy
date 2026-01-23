"""
Settings service layer for the Flet GUI.

This module provides a service wrapper around the existing Settings module,
offering async/Flet-compatible methods for settings management with change
notifications.

Classes
-------
SettingsService
    Service wrapper for settings with change notifications.
"""

import logging
import threading
from typing import Callable, Optional, Set, Any
from dataclasses import asdict

from ..settings import (
    Settings,
    load_settings,
    save_settings,
    TextProcessingSettings,
    create_default_settings,
    SettingsCorruptedError,
    validate_settings,
)
from ..config import (
    accepted_models_whisper,
    accepted_languages_whisper,
)

logger = logging.getLogger(__name__)


class SettingsService:
    """
    Service wrapper for settings management with change notifications.

    This service wraps the existing Settings functionality and provides:
    - Thread-safe settings access
    - Change notification callbacks
    - Settings validation
    - Helper methods for common settings operations

    Attributes
    ----------
    settings
        The current Settings object, or None if not loaded.
    """

    # Available options
    ACCEPTED_MODELS = accepted_models_whisper
    ACCEPTED_LANGUAGES = accepted_languages_whisper
    ACCEPTED_DEVICES = ["cpu", "cuda"]
    ACCEPTED_COMPUTE_TYPES = ["float16", "int8"]
    ACTIVATION_MODES = ["hold", "toggle"]

    def __init__(self):
        """Initialize the settings service."""
        self._settings: Optional[Settings] = None
        self._lock = threading.RLock()
        self._listeners: Set[Callable[[Settings], None]] = set()

    def load(self) -> Optional[Settings]:
        """
        Load settings from disk.

        Returns
        -------
        Settings or None
            The loaded Settings object, or None if loading failed.
        """
        with self._lock:
            self._settings = load_settings()
            if self._settings:
                logger.info(
                    f"Settings loaded: model={self._settings.model_name}, "
                    f"language={self._settings.language}, device={self._settings.device}"
                )
                self._notify()
            return self._settings

    def save(self) -> bool:
        """
        Save current settings to disk.

        Returns
        -------
        bool
            True if save was successful, False otherwise.
        """
        with self._lock:
            if not self._settings:
                logger.warning("No settings to save")
                return False

            try:
                # Use dataclasses.asdict to convert Settings to dictionary
                # This ensures all fields are included, including new ones
                settings_dict = asdict(self._settings)
                result = save_settings(settings_dict)
                if result:
                    logger.info("Settings saved successfully")
                    self._notify()
                return result
            except Exception as e:
                logger.error(f"Failed to save settings: {e}")
                return False

    def load_or_create_default(self) -> Settings:
        """
        Load settings from disk, or create defaults if loading fails.

        Returns
        -------
        Settings
            Always returns a Settings object (never None).
        """
        with self._lock:
            settings = self.load()
            if settings is None:
                logger.info("Could not load settings, creating defaults")
                settings = create_default_settings()
                self._settings = settings
                # Try to save the defaults
                self.save()
            return settings

    def validate_and_apply(self, settings_dict: dict) -> bool:
        """
        Validate a settings dictionary and apply it to the current settings.

        This is useful when receiving settings from UI or external sources.

        Parameters
        ----------
        settings_dict
            Dictionary of settings to validate and apply.

        Returns
        -------
        bool
            True if validation passed and settings were applied, False otherwise.
        """
        with self._lock:
            try:
                validated = validate_settings(settings_dict)
                self._settings = Settings(**validated)
                return True
            except (ValueError, TypeError) as e:
                logger.error(f"Settings validation failed: {e}")
                return False

    def subscribe(self, callback: Callable[[Settings], None]) -> Callable[[], None]:
        """
        Subscribe to settings change notifications.

        Parameters
        ----------
        callback
            Function to call when settings change.

        Returns
        -------
        Callable[[], None]
            Unsubscribe function.
        """
        with self._lock:
            self._listeners.add(callback)

        def unsubscribe():
            with self._lock:
                self._listeners.discard(callback)

        return unsubscribe

    def _notify(self):
        """Notify all subscribers of settings changes."""
        with self._lock:
            listeners = self._listeners.copy()

        if self._settings:
            for callback in listeners:
                try:
                    callback(self._settings)
                except Exception as e:
                    logger.warning(f"Error in settings change callback: {e}")

    # Settings getters
    @property
    def settings(self) -> Optional[Settings]:
        """Get the current Settings object."""
        with self._lock:
            return self._settings

    @property
    def is_loaded(self) -> bool:
        """Check if settings have been loaded."""
        with self._lock:
            return self._settings is not None

    # Individual setting getters/setters
    def get_hotkey(self) -> str:
        """Get the current hotkey."""
        with self._lock:
            return self._settings.hotkey if self._settings else "pause"

    def set_hotkey(self, hotkey: str, notify: bool = True) -> bool:
        """Set the hotkey."""
        with self._lock:
            if not self._settings:
                return False
            self._settings.hotkey = hotkey
            if notify:
                self._notify()
            return True

    def get_history_hotkey(self) -> str:
        """Get the history hotkey."""
        with self._lock:
            return getattr(self._settings, 'history_hotkey', "ctrl+shift+h") if self._settings else "ctrl+shift+h"

    def set_history_hotkey(self, hotkey: str, notify: bool = True) -> bool:
        """Set the history hotkey."""
        with self._lock:
            if not self._settings:
                return False
            self._settings.history_hotkey = hotkey
            if notify:
                self._notify()
            return True

    def get_model_name(self) -> str:
        """Get the current model name."""
        with self._lock:
            return self._settings.model_name if self._settings else "large-v3"

    def set_model_name(self, model_name: str, notify: bool = True) -> bool:
        """Set the model name."""
        with self._lock:
            if not self._settings or model_name not in self.ACCEPTED_MODELS:
                return False
            self._settings.model_name = model_name
            if notify:
                self._notify()
            return True

    def get_language(self) -> str:
        """Get the current language."""
        with self._lock:
            return self._settings.language if self._settings else "en"

    def set_language(self, language: str, notify: bool = True) -> bool:
        """Set the language."""
        with self._lock:
            if not self._settings or language not in self.ACCEPTED_LANGUAGES:
                return False
            self._settings.language = language
            if notify:
                self._notify()
            return True

    def get_device(self) -> str:
        """Get the current device type."""
        with self._lock:
            return self._settings.device if self._settings else "cpu"

    def set_device(self, device: str, notify: bool = True) -> bool:
        """Set the device type."""
        with self._lock:
            if not self._settings or device not in self.ACCEPTED_DEVICES:
                return False
            self._settings.device = device
            if notify:
                self._notify()
            return True

    def get_activation_mode(self) -> str:
        """Get the activation mode."""
        with self._lock:
            return getattr(self._settings, 'activation_mode', 'hold') if self._settings else "hold"

    def set_activation_mode(self, mode: str, notify: bool = True) -> bool:
        """Set the activation mode."""
        with self._lock:
            if not self._settings or mode not in self.ACTIVATION_MODES:
                return False
            self._settings.activation_mode = mode
            if notify:
                self._notify()
            return True

    def get_text_processing_settings(self) -> TextProcessingSettings:
        """Get text processing settings."""
        with self._lock:
            if self._settings:
                return self._settings.get_text_processing_settings()
            return TextProcessingSettings()

    # Validation methods
    @classmethod
    def validate_hotkey(cls, hotkey: str) -> tuple[bool, str]:
        """
        Validate a hotkey string.

        Returns
        -------
        tuple[bool, str]
            (is_valid, error_message)
        """
        if not hotkey or not hotkey.strip():
            return False, "Hotkey cannot be empty"

        # Basic validation - check for valid characters
        valid_parts = {"ctrl", "alt", "shift", "win", "cmd"}
        parts = hotkey.lower().split("+")

        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part in valid_parts or len(part) == 1:
                continue
            # Check for function keys
            if part.startswith("f") and part[1:].isdigit():
                continue
            # Other special keys
            if part in {"pause", "space", "enter", "tab", "escape", "esc",
                        "insert", "home", "end", "pageup", "pagedown",
                        "up", "down", "left", "right",
                        "delete", "backspace"}:
                continue
            return False, f"Invalid key: {part}"

        return True, ""

    @classmethod
    def validate_model(cls, model: str) -> bool:
        """Check if a model name is valid."""
        return model in cls.ACCEPTED_MODELS

    @classmethod
    def validate_language(cls, language: str) -> bool:
        """Check if a language code is valid."""
        return language in cls.ACCEPTED_LANGUAGES

    @classmethod
    def validate_device(cls, device: str) -> bool:
        """Check if a device type is valid."""
        return device in cls.ACCEPTED_DEVICES

    # Helper methods for UI
    def get_model_display_name(self, model: str) -> str:
        """Get a human-readable display name for a model."""
        # Remove common prefixes and format nicely
        display_names = {
            "tiny": "Tiny (fastest, least accurate)",
            "base": "Base",
            "small": "Small",
            "medium": "Medium",
            "large": "Large",
            "large-v1": "Large v1",
            "large-v2": "Large v2",
            "large-v3": "Large v3 (recommended)",
        }
        return display_names.get(model, model)

    def get_language_display_name(self, language: str) -> str:
        """Get a human-readable display name for a language."""
        # Common language codes
        display_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
        }
        return display_names.get(language, language.upper())

    def get_available_models(self) -> list[str]:
        """Get list of available model names."""
        return self.ACCEPTED_MODELS.copy()

    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return self.ACCEPTED_LANGUAGES.copy()
