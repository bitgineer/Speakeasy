"""
Test for function.get_available_models
Comprehensive test suite for getting available models.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.config import get_available_models


class TestGetAvailableModelsFunction:
    """Tests for get_available_models function"""

    def test_get_available_models_returns_list(self):
        """Test that get_available_models returns a list."""
        result = get_available_models()

        assert isinstance(result, list)

    def test_get_available_models_returns_dicts(self):
        """Test that get_available_models returns list of dicts."""
        result = get_available_models()

        if result:
            assert isinstance(result[0], dict)

    def test_get_available_models_has_required_keys(self):
        """Test that models have required keys."""
        result = get_available_models()

        if result:
            model = result[0]
            assert "id" in model or "name" in model or "type" in model

    def test_get_available_models_not_empty(self):
        """Test that get_available_models returns non-empty list."""
        result = get_available_models()

        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
