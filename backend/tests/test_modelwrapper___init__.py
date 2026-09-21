"""
Test for ModelWrapper.__init__
Comprehensive test suite for ModelWrapper initialization.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.models import ModelWrapper, ModelType, TranscriptionResult


class TestModelWrapperInit:
    """Tests for ModelWrapper.__init__"""

    def test_basic_initialization(self):
        """Test basic initialization with valid parameters."""
        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="small",
            device="cuda",
            compute_type="float16",
        )

        assert wrapper.model_type == ModelType.WHISPER
        assert wrapper.model_name == "small"
        assert wrapper.device == "cuda"
        assert wrapper.compute_type == "float16"
        assert wrapper._model is None
        assert wrapper._loaded is False

    def test_initialization_case_insensitive(self):
        """Test that model_type is case-insensitive."""
        wrapper1 = ModelWrapper(model_type="WHISPER", model_name="small")
        wrapper2 = ModelWrapper(model_type="Whisper", model_name="small")
        wrapper3 = ModelWrapper(model_type="whisper", model_name="small")

        assert wrapper1.model_type == ModelType.WHISPER
        assert wrapper2.model_type == ModelType.WHISPER
        assert wrapper3.model_type == ModelType.WHISPER

    def test_initialization_defaults(self):
        """Test default parameter values."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")

        assert wrapper.device == "cuda"
        assert wrapper.compute_type is None

    def test_initialization_various_model_types(self):
        """Test initialization with all supported model types."""
        model_types = [
            ("whisper", ModelType.WHISPER),
            ("parakeet", ModelType.PARAKEET),
            ("canary", ModelType.CANARY),
            ("voxtral", ModelType.VOXTRAL),
        ]

        for type_str, expected_enum in model_types:
            wrapper = ModelWrapper(model_type=type_str, model_name="test")
            assert wrapper.model_type == expected_enum

    def test_initialization_invalid_model_type(self):
        """Test that invalid model type raises ValueError."""
        with pytest.raises(ValueError):
            ModelWrapper(model_type="invalid", model_name="test")

    def test_initialization_model_name_required(self):
        """Test that model_name is required."""
        with pytest.raises(TypeError):
            ModelWrapper(model_type="whisper")

    def test_is_loaded_property_initial(self):
        """Test is_loaded property returns False initially."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")

        assert wrapper.is_loaded is False

    def test_initialization_preserves_model_name(self):
        """Test that model_name is preserved exactly."""
        wrapper = ModelWrapper(model_type="whisper", model_name="Systran/faster-whisper-small")

        assert wrapper.model_name == "Systran/faster-whisper-small"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
