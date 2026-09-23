"""
Test for SettingsService.reset
Comprehensive test suite for resetting settings to defaults.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.settings import AppSettings, HotkeyBinding, SettingsService


class TestSettingsServiceReset:
    """Tests for SettingsService.reset"""

    def test_reset_returns_defaults(self, temp_settings_path):
        """Test that reset returns default settings."""
        service = SettingsService(settings_path=temp_settings_path)

        # First modify some settings
        service.load()
        service._settings.model_type = "whisper"
        service._settings.server_port = 9999

        # Reset
        settings = service.reset()

        assert settings.model_type == "parakeet"  # Default
        assert settings.server_port == 8765  # Default

    def test_reset_clears_custom_settings(self, temp_settings_path):
        """Test that reset clears all custom settings."""
        service = SettingsService(settings_path=temp_settings_path)

        # Load and modify
        service.load()
        service._settings.model_type = "canary"
        service._settings.model_name = "nvidia/canary-1b"
        service._settings.hotkeys = [HotkeyBinding(accelerator="ctrl+space")]

        # Reset
        service.reset()

        # All should be defaults
        assert service._settings.model_type == "parakeet"
        assert service._settings.model_name == "nvidia/parakeet-tdt-0.6b-v3"
        assert service._settings.hotkeys == [HotkeyBinding(accelerator="ctrl+shift+space")]

    def test_reset_saves_to_file(self, temp_settings_path):
        """Test that reset saves defaults to file."""
        service = SettingsService(settings_path=temp_settings_path)

        # Create file with custom settings
        service.load()
        service._settings.model_type = "whisper"
        service.save()

        # Reset
        service.reset()

        # Verify file was updated
        with open(temp_settings_path) as f:
            data = json.load(f)

        assert data["model_type"] == "parakeet"

    def test_reset_returns_new_app_settings_instance(self, temp_settings_path):
        """Test that reset returns a fresh AppSettings instance."""
        service = SettingsService(settings_path=temp_settings_path)

        settings1 = service.reset()
        settings2 = service.reset()

        assert isinstance(settings1, AppSettings)
        assert settings2 is not settings1  # Each reset creates a fresh instance
        assert settings2 is service._settings  # Stored in _settings

    def test_reset_preserves_path(self, temp_settings_path):
        """Test that reset doesn't change the settings path."""
        service = SettingsService(settings_path=temp_settings_path)

        original_path = service.settings_path
        service.reset()

        assert service.settings_path == original_path

    def test_reset_after_corrupted_file(self, temp_settings_path):
        """Test that reset works after file corruption."""
        # Create corrupted file
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_path, "w") as f:
            f.write("corrupted json {{")

        service = SettingsService(settings_path=temp_settings_path)

        # Reset should work
        settings = service.reset()

        assert isinstance(settings, AppSettings)
        assert temp_settings_path.exists()

        # Verify file is now valid JSON
        with open(temp_settings_path) as f:
            data = json.load(f)
        assert "model_type" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
