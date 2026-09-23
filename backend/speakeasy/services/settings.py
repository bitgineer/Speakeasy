"""
Settings service for managing application configuration.

Uses Pydantic for validation and JSON file for persistence.
"""

import json
import logging
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

DEFAULT_COMMAND_PROMPT = (
    "The user will speak an instruction. Carry it out and output only the text to insert, "
    "with no explanation."
)
DEFAULT_HOTKEY = "ctrl+shift+space"


class ProcessingMode(StrEnum):
    """How a transcript is processed before it is inserted."""

    WRITE = "write"
    COMMAND = "command"
    DICTATE = "dictate"


class ProviderKind(StrEnum):
    """Transport family of an OpenAI-compatible chat provider."""

    LOCAL = "local"
    OPENAI = "openai"
    GROQ = "groq"
    CUSTOM = "custom"


class AppMatch(BaseModel):
    """One rule that ties a tone profile to an app identifier or a window title."""

    field: Literal["app", "title"]
    pattern: str = Field(..., min_length=1, max_length=200)


class ToneProfile(BaseModel):
    """A rewrite tone used in write mode when one of its matches fires."""

    name: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(default="", max_length=4000)
    matches: list[AppMatch] = Field(default_factory=list)


class LlmProvider(BaseModel):
    """One OpenAI-compatible chat endpoint. Credentials live in secrets.json, not here."""

    id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", max_length=50)
    label: str = Field(default="", max_length=100)
    kind: ProviderKind = ProviderKind.LOCAL
    base_url: str = Field(default="", max_length=500)
    model: str = Field(default="", max_length=200)
    timeout_seconds: float = Field(default=20.0, ge=1.0, le=120.0)


class HotkeyBinding(BaseModel):
    """A global chord. ``mode`` None records in ``active_mode`` at press time."""

    accelerator: str = Field(..., pattern=r"^[a-zA-Z0-9+]+$", max_length=50)
    trigger: Literal["toggle", "push-to-talk"] = "toggle"
    mode: ProcessingMode | None = None


def _default_tone() -> ToneProfile:
    return ToneProfile(name="Default")


def _default_hotkeys() -> list[HotkeyBinding]:
    return [HotkeyBinding(accelerator=DEFAULT_HOTKEY)]


class AppSettings(BaseModel):
    """Application settings with validation."""

    # Model settings
    model_type: str = Field(default="parakeet", description="ASR model type")
    model_name: str = Field(
        default="nvidia/parakeet-tdt-0.6b-v3",
        description="Model name or HuggingFace repo ID",
    )
    compute_type: str = Field(default="float16", description="Compute precision")
    device: Literal["cuda", "cpu"] = Field(
        default="cuda", description="Device to run on (cuda/cpu)"
    )
    language: str = Field(default="auto", description="Language code or 'auto'")

    # Audio settings
    device_name: str | None = Field(default=None, description="Audio input device name")

    # Hotkey settings
    hotkey: str = Field(default="ctrl+shift+space", description="Global hotkey combination")
    hotkey_mode: Literal["toggle", "push-to-talk"] = Field(
        default="toggle", description="Hotkey mode: 'toggle' or 'push-to-talk'"
    )

    # Processing settings
    active_mode: ProcessingMode = Field(
        default=ProcessingMode.DICTATE, description="Mode the primary hotkey records in"
    )
    active_provider_id: str = Field(
        default="",
        max_length=50,
        description="Provider used by LLM modes. Empty means none, because the update "
        "endpoint filters None and cannot clear a nullable field.",
    )
    default_tone: ToneProfile = Field(
        default_factory=_default_tone, description="Tone used when no profile matches"
    )
    tone_profiles: list[ToneProfile] = Field(
        default_factory=list, description="Per-app tone profiles for write mode"
    )
    command_prompt: str = Field(
        default=DEFAULT_COMMAND_PROMPT, max_length=4000, description="System prompt for command mode"
    )
    providers: list[LlmProvider] = Field(
        default_factory=list, description="Configured OpenAI-compatible providers"
    )
    hotkeys: list[HotkeyBinding] = Field(
        default_factory=_default_hotkeys, description="Global hotkey bindings"
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
    custom_filler_words: list[str] | None = Field(
        default=None, description="Additional filler words to remove"
    )

    # Diagnostics
    debug_logging: bool = Field(default=False, description="Enable verbose backend logging")

    # Live transcription settings
    live_transcription: bool = Field(
        default=False, description="Enable real-time partial transcription while recording"
    )
    live_chunk_seconds: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Interval in seconds between live transcription updates",
    )
    live_auto_paste: bool = Field(
        default=False, description="Auto-paste live transcripts into active window"
    )

    # Server settings
    server_port: int = Field(default=8765, description="Backend server port")

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_hotkey(cls, data: object) -> object:
        """Fold the legacy single-hotkey fields into ``hotkeys`` when the list is absent."""
        if not isinstance(data, dict) or "hotkeys" in data:
            return data
        if "hotkey" not in data and "hotkey_mode" not in data:
            return data
        binding = {
            "accelerator": data.get("hotkey") or DEFAULT_HOTKEY,
            "trigger": data.get("hotkey_mode") or "toggle",
            "mode": None,
        }
        return {**data, "hotkeys": [binding]}

    @model_validator(mode="after")
    def _validate_unique_groups(self) -> "AppSettings":
        """Reject duplicate provider ids, tone names, and hotkey accelerators.

        ``active_provider_id`` is deliberately not checked against ``providers``. ``load()``
        resets every setting when validation fails, so a dangling id from a deleted provider
        must not wipe the file. The resolver degrades the unknown id instead.
        """
        provider_ids = [provider.id for provider in self.providers]
        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError("Provider ids must be unique")
        tone_names = [profile.name for profile in self.tone_profiles]
        if len(tone_names) != len(set(tone_names)):
            raise ValueError("Tone profile names must be unique")
        accelerators = [binding.accelerator for binding in self.hotkeys]
        if len(accelerators) != len(set(accelerators)):
            raise ValueError("Hotkey accelerators must be unique")
        return self


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
        self._settings: AppSettings | None = None

    def load(self) -> AppSettings:
        """
        Load settings from file, creating defaults if needed.

        Returns:
            The loaded or default settings
        """
        if self.settings_path.exists():
            try:
                with open(self.settings_path) as f:
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
