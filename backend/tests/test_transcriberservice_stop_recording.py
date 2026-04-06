"""
Test for TranscriberService.stop_recording
Comprehensive test suite for stopping recording.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState, RecordingResult


class TestTranscriberServiceStopRecording:
    """Tests for TranscriberService.stop_recording"""

    @pytest.fixture
    def service_recording(self):
        """Create a service in recording state."""
        service = TranscriberService()
        service._state = TranscriberState.RECORDING
        service._stream = Mock()
        service._recording_start_time = 0
        service._recording_samplerate = 16000
        service._audio_buffer = [np.array([0.1, 0.2, 0.3], dtype=np.float32)]
        return service

    def test_stop_recording_not_recording_raises(self):
        """Test that stop_recording raises when not recording."""
        service = TranscriberService()
        service._state = TranscriberState.IDLE

        with pytest.raises(RuntimeError, match="Not recording"):
            service.stop_recording()

    def test_stop_recording_stops_stream(self, service_recording):
        """Test that stop_recording stops the audio stream."""
        service = service_recording

        with patch("numpy.concatenate", return_value=np.array([0.1, 0.2, 0.3])):
            service.stop_recording()

        service._stream.stop.assert_called_once()
        service._stream.close.assert_called_once()

    def test_stop_recording_returns_recording_result(self, service_recording):
        """Test that stop_recording returns a RecordingResult."""
        service = service_recording

        with patch("numpy.concatenate", return_value=np.array([0.1, 0.2, 0.3])):
            result = service.stop_recording()

        assert isinstance(result, RecordingResult)
        assert result.sample_rate == 16000

    def test_stop_recording_empty_buffer_raises(self, service_recording):
        """Test that stop_recording raises if buffer is empty."""
        service = service_recording
        service._audio_buffer = []

        with pytest.raises(RuntimeError, match="No audio recorded"):
            service.stop_recording()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
