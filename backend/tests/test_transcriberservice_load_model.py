"""
Test for TranscriberService.load_model
Comprehensive test suite for loading models.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState


class TestTranscriberServiceLoadModel:
    """Tests for TranscriberService.load_model"""

    def test_load_model_sets_loading_state(self):
        """Test that load_model sets state to LOADING."""
        service = TranscriberService()
        callback = Mock()
        service._on_state_change = callback

        with patch("speakeasy.core.transcriber.ModelWrapper"):
            with patch.object(service, "_set_state") as mock_set_state:
                try:
                    service.load_model("whisper", "small")
                except:
                    pass
                # Should have called with LOADING
                assert any(
                    call[0][0] == TranscriberState.LOADING for call in mock_set_state.call_args_list
                )

    def test_load_model_saves_args(self):
        """Test that load_model saves arguments for reload."""
        service = TranscriberService()

        with patch("speakeasy.core.transcriber.ModelWrapper"):
            service.load_model("whisper", "small", device="cuda", compute_type="float16")

        assert hasattr(service, "_last_load_args")
        assert service._last_load_args["model_type"] == "whisper"
        assert service._last_load_args["model_name"] == "small"

    def test_load_model_unloads_existing(self):
        """Test that load_model unloads existing model."""
        service = TranscriberService()
        service._model = Mock()
        service._model.is_loaded = True

        with patch("speakeasy.core.transcriber.ModelWrapper") as MockWrapper:
            mock_instance = Mock()
            MockWrapper.return_value = mock_instance

            service.load_model("whisper", "small")

            service._model.unload.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
