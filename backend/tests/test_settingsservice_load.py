"""
Test for SettingsService.load
Comprehensive test suite for loading settings.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.settings import SettingsService, AppSettings


@pytest.fixture
def temp_settings_path():
    """Create a temporary settings file path."""
    temp_dir = tempfile.mkdtemp()
    settings_path = Path(temp_dir) / "settings.json"
    yield settings_path
    # Cleanup
    if settings_path.exists():
        settings_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestSettingsServiceLoad:
    """Tests for SettingsService.load"""

    def test_load_creates_defaults_if_file_not_exists(self, temp_settings_path):
        """Test that load creates default settings if file doesn't exist."""
        service = SettingsService(settings_path=temp_settings_path)

        settings = service.load()

        assert isinstance(settings, AppSettings)
        assert temp_settings_path.exists()  # Should create file

    def test_load_reads_existing_file(self, temp_settings_path):
        """Test that load reads existing settings file."""
        # Create a settings file
        custom_settings = {
            "model_type": "whisper",
            "model_name": "small",
            "server_port": 9999,
        }
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_path, "w") as f:
            json.dump(custom_settings, f)

        service = SettingsService(settings_path=temp_settings_path)
        settings = service.load()

        assert settings.model_type == "whisper"
        assert settings.model_name == "small"
        assert settings.server_port == 9999

    def test_load_handles_corrupted_file(self, temp_settings_path):
        """Test that load handles corrupted JSON gracefully."""
        # Create corrupted file
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_path, "w") as f:
            f.write("not valid json {{")

        service = SettingsService(settings_path=temp_settings_path)
        settings = service.load()

        # Should return defaults
        assert isinstance(settings, AppSettings)
        assert settings.model_type == "parakeet"  # Default value

    def test_load_returns_cached_settings(self, temp_settings_path):
        """Test that load returns cached settings if already loaded."""
        service = SettingsService(settings_path=temp_settings_path)

        settings1 = service.load()
        settings2 = service.load()

        assert settings1 is settings2  # Same object

    def test_load_creates_parent_directories(self, temp_settings_path):
        """Test that load creates parent directories if needed."""
        deep_path = temp_settings_path.parent / "nested" / "deep" / "settings.json"
        service = SettingsService(settings_path=deep_path)

        service.load()

        assert deep_path.parent.exists()
        assert deep_path.exists()

    def test_load_preserves_unknown_fields(self, temp_settings_path):
        """Test that load preserves extra fields in settings file."""
        custom_settings = {
            "model_type": "whisper",
            "custom_field": "custom_value",
            "another_field": 123,
        }
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_path, "w") as f:
            json.dump(custom_settings, f)

        service = SettingsService(settings_path=temp_settings_path)
        settings = service.load()

        # Should not crash on unknown fields
        assert settings.model_type == "whisper"

    def test_load_partial_settings(self, temp_settings_path):
        """Test loading file with partial settings."""
        partial_settings = {"model_type": "canary"}
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_path, "w") as f:
            json.dump(partial_settings, f)

        service = SettingsService(settings_path=temp_settings_path)
        settings = service.load()

        assert settings.model_type == "canary"
        assert settings.model_name == "nvidia/parakeet-tdt-0.6b-v3"  # Default

    def test_load_empty_file(self, temp_settings_path):
        """Test loading an empty file."""
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        temp_settings_path.write_text("")

        service = SettingsService(settings_path=temp_settings_path)
        settings = service.load()

        # Should return defaults
        assert isinstance(settings, AppSettings)

    def test_load_file_permission_error(self, temp_settings_path):
        """Test handling of file permission errors."""
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_path, "w") as f:
            json.dump({"model_type": "whisper"}, f)

        # Make file unreadable (on Unix)
        if os.name != "nt":
            os.chmod(temp_settings_path, 0o000)
            try:
                service = SettingsService(settings_path=temp_settings_path)
                settings = service.load()

                # Should return defaults on error
                assert isinstance(settings, AppSettings)
            finally:
                os.chmod(temp_settings_path, 0o644)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
