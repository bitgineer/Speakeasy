"""
Test for TranscriberService.unload_model
Comprehensive test suite for unloading models.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState


class TestTranscriberServiceUnloadModel:
    """Tests for TranscriberService.unload_model"""

    def test_unload_model_with_loaded_model(self):
        """Test unloading a loaded model."""
        service = TranscriberService()
        service._model = Mock()
        service._model.is_loaded = True
        service._state = TranscriberState.READY

        service.unload_model()

        service._model.unload.assert_called_once()
        assert service._model is None

    def test_unload_model_no_model(self):
        """Test unloading when no model is loaded."""
        service = TranscriberService()
        service._model = None
        service._state = TranscriberState.READY

        # Should not raise
        service.unload_model()

        assert service._model is None

    def test_unload_model_sets_idle_state(self):
        """Test that unload_model sets state to IDLE."""
        service = TranscriberService()
        service._model = Mock()
        service._state = TranscriberState.READY

        with patch.object(service, "_set_state") as mock_set_state:
            service.unload_model()
            mock_set_state.assert_called_with(TranscriberState.IDLE)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
