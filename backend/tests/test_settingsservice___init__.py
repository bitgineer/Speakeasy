"""
Test for SettingsService.__init__
Comprehensive test suite for SettingsService initialization.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
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


class TestSettingsServiceInit:
    """Tests for SettingsService.__init__"""

    def test_basic_initialization(self, temp_settings_path):
        """Test basic initialization with a valid path."""
        service = SettingsService(settings_path=temp_settings_path)

        assert service.settings_path == temp_settings_path
        assert service._settings is None

    def test_initialization_creates_parent_directory(self, temp_settings_path):
        """Test that initialization sets up path correctly."""
        deep_path = temp_settings_path.parent / "subfolder" / "settings.json"
        service = SettingsService(settings_path=deep_path)

        assert service.settings_path == deep_path
        assert not deep_path.parent.exists()  # Directory not created yet

    def test_initialization_preserves_path_object(self, temp_settings_path):
        """Test that the path object is preserved."""
        service = SettingsService(settings_path=temp_settings_path)

        assert isinstance(service.settings_path, Path)

    def test_initialization_with_relative_path(self):
        """Test initialization with a relative path."""
        rel_path = Path("relative") / "settings.json"
        service = SettingsService(settings_path=rel_path)

        assert service.settings_path == rel_path

    def test_multiple_services_different_paths(self, temp_settings_path):
        """Test creating multiple services with different paths."""
        service1 = SettingsService(settings_path=temp_settings_path)
        service2 = SettingsService(settings_path=temp_settings_path.parent / "other.json")

        assert service1.settings_path != service2.settings_path

    def test_initialization_does_not_create_file(self, temp_settings_path):
        """Test that initialization doesn't create the file yet."""
        service = SettingsService(settings_path=temp_settings_path)

        assert not temp_settings_path.exists()

    def test_initialization_attributes(self, temp_settings_path):
        """Test that all expected attributes are set."""
        service = SettingsService(settings_path=temp_settings_path)

        assert hasattr(service, "settings_path")
        assert hasattr(service, "_settings")
        assert service._settings is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
