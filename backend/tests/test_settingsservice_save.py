"""
Test for SettingsService.save
Comprehensive test suite for saving settings.
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


class TestSettingsServiceSave:
    """Tests for SettingsService.save"""

    def test_save_creates_file(self, temp_settings_path):
        """Test that save creates the settings file."""
        service = SettingsService(settings_path=temp_settings_path)
        service.load()  # Load defaults
        service.save()

        assert temp_settings_path.exists()

    def test_save_writes_valid_json(self, temp_settings_path):
        """Test that save writes valid JSON."""
        service = SettingsService(settings_path=temp_settings_path)
        service.load()
        service.save()

        with open(temp_settings_path, "r") as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert "model_type" in data

    def test_save_preserves_settings(self, temp_settings_path):
        """Test that save preserves all settings."""
        service = SettingsService(settings_path=temp_settings_path)
        service.load()

        # Modify a setting
        service._settings.model_type = "whisper"
        service._settings.server_port = 9999

        service.save()

        # Load again and verify
        service2 = SettingsService(settings_path=temp_settings_path)
        settings = service2.load()

        assert settings.model_type == "whisper"
        assert settings.server_port == 9999

    def test_save_creates_parent_directories(self, temp_settings_path):
        """Test that save creates parent directories."""
        deep_path = temp_settings_path.parent / "nested" / "save" / "settings.json"
        service = SettingsService(settings_path=deep_path)
        service.load()
        service.save()

        assert deep_path.exists()

    def test_save_without_load(self, temp_settings_path):
        """Test that save works even without explicit load."""
        service = SettingsService(settings_path=temp_settings_path)
        service.save()

        assert temp_settings_path.exists()

    def test_save_overwrites_existing(self, temp_settings_path):
        """Test that save overwrites existing file."""
        # Create initial file
        temp_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_path, "w") as f:
            json.dump({"model_type": "old"}, f)

        service = SettingsService(settings_path=temp_settings_path)
        service.load()
        service._settings.model_type = "new"
        service.save()

        with open(temp_settings_path, "r") as f:
            data = json.load(f)

        assert data["model_type"] == "new"

    def test_save_formatting(self, temp_settings_path):
        """Test that save produces formatted JSON with indentation."""
        service = SettingsService(settings_path=temp_settings_path)
        service.load()
        service.save()

        content = temp_settings_path.read_text()

        # Should have newlines (formatted)
        assert "\n" in content
        # Should have indentation
        assert "  " in content or "\t" in content

    def test_save_all_settings_fields(self, temp_settings_path):
        """Test that save includes all settings fields."""
        service = SettingsService(settings_path=temp_settings_path)
        service.load()
        service.save()

        with open(temp_settings_path, "r") as f:
            data = json.load(f)

        # Check all expected fields are present
        expected_fields = [
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
            "always_show_indicator",
            "theme",
            "enable_text_cleanup",
            "custom_filler_words",
            "enable_grammar_correction",
            "grammar_model",
            "grammar_device",
            "server_port",
        ]

        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
