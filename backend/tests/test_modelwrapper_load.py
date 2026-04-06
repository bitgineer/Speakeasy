"""
Test for ModelWrapper.load
Comprehensive test suite for loading models.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.models import ModelWrapper, ModelType, TranscriptionResult


class TestModelWrapperLoad:
    """Tests for ModelWrapper.load"""

    def test_load_already_loaded_model(self):
        """Test that loading an already loaded model returns early."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        wrapper._loaded = True

        with patch.object(wrapper, "_load_whisper") as mock_load:
            wrapper.load()
            mock_load.assert_not_called()

    def test_load_sets_loaded_flag(self):
        """Test that load sets _loaded flag to True."""
        wrapper = ModelWrapper(model_type="whisper", model_name="tiny")

        with patch.object(wrapper, "_load_whisper"):
            wrapper.load()
            assert wrapper._loaded is True

    def test_load_whisper_calls_correct_loader(self):
        """Test that load calls _load_whisper for whisper models."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")

        with patch.object(wrapper, "_load_whisper") as mock_load_whisper:
            with patch.object(wrapper, "_load_parakeet") as mock_load_parakeet:
                wrapper.load()
                mock_load_whisper.assert_called_once()
                mock_load_parakeet.assert_not_called()

    def test_load_parakeet_calls_correct_loader(self):
        """Test that load calls _load_parakeet for parakeet models."""
        wrapper = ModelWrapper(model_type="parakeet", model_name="nvidia/parakeet-tdt-0.6b-v3")

        with patch.object(wrapper, "_load_whisper") as mock_load_whisper:
            with patch.object(wrapper, "_load_parakeet") as mock_load_parakeet:
                wrapper.load()
                mock_load_whisper.assert_not_called()
                mock_load_parakeet.assert_called_once()

    def test_load_canary_calls_correct_loader(self):
        """Test that load calls _load_canary for canary models."""
        wrapper = ModelWrapper(model_type="canary", model_name="nvidia/canary-1b-v2")

        with patch.object(wrapper, "_load_whisper") as mock_load_whisper:
            with patch.object(wrapper, "_load_canary") as mock_load_canary:
                wrapper.load()
                mock_load_whisper.assert_not_called()
                mock_load_canary.assert_called_once()

    def test_load_voxtral_calls_correct_loader(self):
        """Test that load calls _load_voxtral for voxtral models."""
        wrapper = ModelWrapper(model_type="voxtral", model_name="mistralai/Voxtral-Mini-3B-2507")

        with patch.object(wrapper, "_load_whisper") as mock_load_whisper:
            with patch.object(wrapper, "_load_voxtral") as mock_load_voxtral:
                wrapper.load()
                mock_load_whisper.assert_not_called()
                mock_load_voxtral.assert_called_once()

    def test_load_with_progress_callback(self):
        """Test that load accepts progress callback."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        progress_callback = Mock(return_value=True)

        with patch.object(wrapper, "_load_whisper") as mock_load:
            wrapper.load(progress_callback=progress_callback)
            mock_load.assert_called_once()

    def test_load_unknown_model_type_raises_error(self):
        """Test that loading unknown model type raises ValueError."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        # Manually set an invalid type
        wrapper.model_type = "invalid"

        with pytest.raises(ValueError, match="Unknown model type"):
            wrapper.load()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
