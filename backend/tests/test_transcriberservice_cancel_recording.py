"""
Test for TranscriberService.cancel_recording
Comprehensive test suite for canceling recordings.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState


class TestTranscriberServiceCancelRecording:
    """Tests for TranscriberService.cancel_recording"""

    def test_cancel_recording_not_recording(self):
        """Test cancel when not recording does nothing."""
        service = TranscriberService()
        service._state = TranscriberState.IDLE

        # Should not raise
        service.cancel_recording()

        assert service._state == TranscriberState.IDLE

    def test_cancel_recording_while_recording(self):
        """Test cancel while recording."""
        service = TranscriberService()
        service._state = TranscriberState.RECORDING
        service._stream = Mock()

        with patch.object(service, "_cleanup_recording_state") as mock_cleanup:
            service.cancel_recording()

            mock_cleanup.assert_called_once()

    def test_cancel_recording_resets_state(self):
        """Test that cancel resets state to IDLE or READY."""
        service = TranscriberService()
        service._state = TranscriberState.RECORDING
        service._model = Mock()
        service._model.is_loaded = True

        with patch.object(service, "_cleanup_recording_state"):
            service.cancel_recording()

        assert service._state in [TranscriberState.IDLE, TranscriberState.READY]

    def test_cancel_recording_no_model_loaded(self):
        """Test cancel when no model is loaded."""
        service = TranscriberService()
        service._state = TranscriberState.RECORDING
        service._stream = Mock()

        with patch.object(service, "_cleanup_recording_state"):
            service.cancel_recording()

        assert service._state == TranscriberState.IDLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
