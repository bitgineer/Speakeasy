"""
Settings service for managing application configuration.

Uses Pydantic for validation and JSON file for persistence.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AppSettings(BaseModel):
    """Application settings with validation."""

    # Model settings
    model_type: str = Field(default="parakeet", description="ASR model type")
    model_name: str = Field(
        default="nvidia/parakeet-tdt-0.6b-v3",
        description="Model name or HuggingFace repo ID",
    )
    compute_type: str = Field(default="float16", description="Compute precision")
    device: str = Field(default="cuda", description="Device to run on (cuda/cpu)")
    language: str = Field(default="auto", description="Language code or 'auto'")

    # Audio settings
    device_name: Optional[str] = Field(default=None, description="Audio input device name")

    # Hotkey settings
    hotkey: str = Field(default="ctrl+shift+space", description="Global hotkey combination")
    hotkey_mode: str = Field(
        default="toggle", description="Hotkey mode: 'toggle' or 'push-to-talk'"
    )

    # UI settings
    auto_paste: bool = Field(default=True, description="Automatically paste after transcription")
    show_recording_indicator: bool = Field(default=True, description="Show recording overlay")
    always_show_indicator: bool = Field(
        default=True, description="Keep indicator visible when idle"
    )
    theme: str = Field(default="default", description="UI theme name")

    # Text cleanup settings
    enable_text_cleanup: bool = Field(
        default=True, description="Remove filler words from transcription"
    )
    custom_filler_words: Optional[list[str]] = Field(
        default=None, description="Additional filler words to remove"
    )

    # Grammar correction settings
    enable_grammar_correction: bool = Field(
        default=False, description="Enable AI grammar correction"
    )
    grammar_model: str = Field(
        default="vennify/t5-base-grammar-correction",
        description="Grammar correction model name",
    )
    grammar_device: str = Field(
        default="auto",
        description="Device for grammar model (auto/cuda/cpu)",
    )

    # Server settings
    server_port: int = Field(default=8765, description="Backend server port")


class SettingsService:
    """
    Manages application settings with persistence.

    Settings are stored in JSON format and validated with Pydantic.
    """

    def __init__(self, settings_path: Path):
        """
        Initialize the settings service.

        Args:
            settings_path: Path to the settings JSON file
        """
        self.settings_path = settings_path
        self._settings: Optional[AppSettings] = None

    def load(self) -> AppSettings:
        """
        Load settings from file, creating defaults if needed.

        Returns:
            The loaded or default settings
        """
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    data = json.load(f)
                self._settings = AppSettings(**data)
                logger.info(f"Loaded settings from {self.settings_path}")
            except Exception as e:
                logger.error(f"Error loading settings: {e}, using defaults")
                self._settings = AppSettings()
        else:
            logger.warning(f"No settings file found at {self.settings_path}, creating defaults")
            self._settings = AppSettings()
            # Save defaults immediately to ensure file exists and directory is created
            self.save()

        return self._settings

    def save(self) -> None:
        """Save current settings to file."""
        if not self._settings:
            self._settings = AppSettings()

        # Ensure directory exists
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.settings_path, "w") as f:
            json.dump(self._settings.model_dump(), f, indent=2)

        logger.info(f"Settings saved to {self.settings_path}")

    def get(self) -> AppSettings:
        """
        Get current settings, loading if needed.

        Returns:
            The current settings
        """
        if not self._settings:
            self.load()
        return self._settings

    def update(self, **kwargs) -> AppSettings:
        """
        Update settings with new values.

        Args:
            **kwargs: Settings fields to update

        Returns:
            The updated settings
        """
        if not self._settings:
            self.load()

        # Create new settings with updates
        current_dict = self._settings.model_dump()
        current_dict.update(kwargs)
        self._settings = AppSettings(**current_dict)

        # Persist changes
        self.save()

        return self._settings

    def reset(self) -> AppSettings:
        """
        Reset settings to defaults.

        Returns:
            The default settings
        """
        self._settings = AppSettings()
        self.save()
        return self._settings

    def to_dict(self) -> dict:
        """
        Get settings as dictionary.

        Returns:
            Settings dictionary
        """
        return self.get().model_dump()


# Default data directory
def get_data_dir() -> Path:
    """Get the default data directory (~/.speakeasy)."""
    return Path.home() / ".speakeasy"


def get_default_settings_path() -> Path:
    """Get the default settings file path."""
    return get_data_dir() / "settings.json"


def get_default_db_path() -> Path:
    """Get the default database file path."""
    return get_data_dir() / "speakeasy.db"
