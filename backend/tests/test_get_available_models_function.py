"""
Test for function.get_available_models
Comprehensive test suite for getting available models.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.config import get_available_models


class TestGetAvailableModelsFunction:
    """Tests for get_available_models function"""

    def test_get_available_models_returns_list(self):
        """Test that get_available_models returns a list."""
        result = get_available_models("whisper")

        assert isinstance(result, list)

    def test_get_available_models_returns_strings(self):
        """Test that get_available_models returns model name strings."""
        result = get_available_models("whisper")

        assert result
        assert all(isinstance(name, str) for name in result)

    def test_get_available_models_entries_are_non_empty(self):
        """Test that each returned model name is non-empty."""
        result = get_available_models("whisper")

        assert result
        assert all(name for name in result)

    def test_get_available_models_not_empty(self):
        """Test that get_available_models returns non-empty list for a known type."""
        result = get_available_models("whisper")

        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
