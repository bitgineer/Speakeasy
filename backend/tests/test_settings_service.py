"""
Tests for the SettingsService.

Tests cover loading, saving, updating, and resetting settings,
as well as helper functions for default paths.
"""

import json
from pathlib import Path

import pytest

from speakeasy.services.settings import (
    AppSettings,
    SettingsService,
    get_data_dir,
    get_default_db_path,
    get_default_settings_path,
)


@pytest.fixture
def settings_service(tmp_path: Path) -> SettingsService:
    """Create a SettingsService using a temporary path."""
    settings_path = tmp_path / "settings.json"
    return SettingsService(settings_path)


class TestSettingsServiceLoad:
    """Tests for loading settings."""

    def test_load_creates_default(self, settings_service: SettingsService):
        """Loading when no file exists creates default settings and saves them."""
        assert not settings_service.settings_path.exists()

        settings = settings_service.load()

        assert settings is not None
        assert isinstance(settings, AppSettings)
        # File should be created with defaults
        assert settings_service.settings_path.exists()

    def test_load_existing_file(self, tmp_path: Path):
        """Loading reads settings from existing JSON file."""
        settings_path = tmp_path / "settings.json"
        custom_settings = {
            "model_type": "whisper",
            "model_name": "openai/whisper-large-v3",
            "compute_type": "int8",
            "device": "cpu",
            "language": "en",
            "device_name": "Microphone (USB)",
            "hotkey": "f4",
            "hotkey_mode": "push-to-talk",
            "auto_paste": False,
            "show_recording_indicator": False,
            "server_port": 9000,
        }
        with open(settings_path, "w") as f:
            json.dump(custom_settings, f)

        service = SettingsService(settings_path)
        settings = service.load()

        assert settings.model_type == "whisper"
        assert settings.model_name == "openai/whisper-large-v3"
        assert settings.compute_type == "int8"
        assert settings.device == "cpu"
        assert settings.language == "en"
        assert settings.device_name == "Microphone (USB)"
        assert settings.hotkey == "f4"
        assert settings.hotkey_mode == "push-to-talk"
        assert settings.auto_paste is False
        assert settings.show_recording_indicator is False
        assert settings.server_port == 9000


class TestSettingsServiceSave:
    """Tests for saving settings."""

    def test_save_creates_directory(self, tmp_path: Path):
        """Save creates parent directories if they don't exist."""
        nested_path = tmp_path / "nested" / "deep" / "settings.json"
        service = SettingsService(nested_path)

        # Load to initialize settings, then save
        service.load()

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_save_creates_file(self, settings_service: SettingsService):
        """Save writes settings to JSON file correctly."""
        settings_service.load()
        settings_service._settings.model_type = "canary"
        settings_service._settings.server_port = 8888

        settings_service.save()

        with open(settings_service.settings_path, "r") as f:
            data = json.load(f)

        assert data["model_type"] == "canary"
        assert data["server_port"] == 8888


class TestSettingsServiceGet:
    """Tests for getting settings."""

    def test_get_lazy_loads(self, settings_service: SettingsService):
        """get() calls load() if settings haven't been loaded yet."""
        assert settings_service._settings is None

        settings = settings_service.get()

        assert settings is not None
        assert settings_service._settings is not None
        assert isinstance(settings, AppSettings)


class TestSettingsServiceUpdate:
    """Tests for updating settings."""

    def test_update_partial(self, settings_service: SettingsService):
        """Update modifies only specified fields."""
        settings_service.load()
        original_model_name = settings_service._settings.model_name

        updated = settings_service.update(
            hotkey="f8",
            auto_paste=False,
        )

        assert updated.hotkey == "f8"
        assert updated.auto_paste is False
        # Other fields unchanged
        assert updated.model_name == original_model_name

    def test_update_persists(self, tmp_path: Path):
        """Update writes changes to file that persist across instances."""
        settings_path = tmp_path / "settings.json"
        service1 = SettingsService(settings_path)
        service1.load()

        service1.update(
            model_type="voxtral",
            language="fr",
        )

        # Create new service instance and load
        service2 = SettingsService(settings_path)
        settings = service2.load()

        assert settings.model_type == "voxtral"
        assert settings.language == "fr"


class TestSettingsServiceReset:
    """Tests for resetting settings."""

    def test_reset_to_defaults(self, settings_service: SettingsService):
        """Reset restores all fields to default values."""
        settings_service.load()
        settings_service.update(
            model_type="whisper",
            model_name="custom-model",
            compute_type="int8",
            device="cpu",
            language="de",
            hotkey="f12",
            hotkey_mode="push-to-talk",
            auto_paste=False,
            show_recording_indicator=False,
            server_port=9999,
        )

        reset_settings = settings_service.reset()

        # Verify all defaults
        assert reset_settings.model_type == "parakeet"
        assert reset_settings.model_name == "nvidia/parakeet-tdt-0.6b-v3"
        assert reset_settings.compute_type == "float16"
        assert reset_settings.device == "cuda"
        assert reset_settings.language == "auto"
        assert reset_settings.device_name is None
        assert reset_settings.hotkey == "ctrl+shift+space"
        assert reset_settings.hotkey_mode == "toggle"
        assert reset_settings.auto_paste is True
        assert reset_settings.show_recording_indicator is True
        assert reset_settings.server_port == 8765


class TestSettingsServiceToDict:
    """Tests for dictionary serialization."""

    def test_to_dict_serialization(self, settings_service: SettingsService):
        """to_dict() returns correct dictionary representation."""
        settings_service.load()
        settings_service.update(
            model_type="canary",
            server_port=7777,
        )

        result = settings_service.to_dict()

        assert isinstance(result, dict)
        assert result["model_type"] == "canary"
        assert result["server_port"] == 7777
        # All 11 fields present
        expected_keys = {
            "model_type",
            "model_name",
            "compute_type",
            "device",
            "language",
            "device_name",
            "hotkey",
            "hotkey_mode",
            "auto_paste",
            "show_recording_indicator",
            "server_port",
        }
        assert set(result.keys()) == expected_keys


class TestAppSettingsDefaults:
    """Tests for AppSettings default values."""

    def test_default_values(self):
        """All AppSettings fields have correct default values."""
        settings = AppSettings()

        assert settings.model_type == "parakeet"
        assert settings.model_name == "nvidia/parakeet-tdt-0.6b-v3"
        assert settings.compute_type == "float16"
        assert settings.device == "cuda"
        assert settings.language == "auto"
        assert settings.device_name is None
        assert settings.hotkey == "ctrl+shift+space"
        assert settings.hotkey_mode == "toggle"
        assert settings.auto_paste is True
        assert settings.show_recording_indicator is True
        assert settings.server_port == 8765


class TestCorruptedFile:
    """Tests for handling corrupted settings files."""

    def test_corrupted_file_uses_defaults(self, tmp_path: Path):
        """Invalid JSON file falls back to default settings."""
        settings_path = tmp_path / "settings.json"
        # Write invalid JSON
        with open(settings_path, "w") as f:
            f.write("{ invalid json content }")

        service = SettingsService(settings_path)
        settings = service.load()

        # Should use defaults
        assert settings.model_type == "parakeet"
        assert settings.model_name == "nvidia/parakeet-tdt-0.6b-v3"
        assert settings.server_port == 8765


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_helper_functions(self):
        """Helper functions return correct paths."""
        data_dir = get_data_dir()
        settings_path = get_default_settings_path()
        db_path = get_default_db_path()

        # Verify types
        assert isinstance(data_dir, Path)
        assert isinstance(settings_path, Path)
        assert isinstance(db_path, Path)

        # Verify structure
        assert data_dir == Path.home() / ".speakeasy"
        assert settings_path == data_dir / "settings.json"
        assert db_path == data_dir / "speakeasy.db"

        # Verify relationships
        assert settings_path.parent == data_dir
        assert db_path.parent == data_dir
