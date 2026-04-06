"""
Test for TranscriberService.stop_and_transcribe
Comprehensive test suite for stop and transcribe functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState, TranscriptionResult


class TestTranscriberServiceStopAndTranscribe:
    """Tests for TranscriberService.stop_and_transcribe"""

    @pytest.fixture
    def service_with_model(self):
        """Create a service with a loaded model."""
        service = TranscriberService()
        service._state = TranscriberState.RECORDING
        service._stream = Mock()
        service._recording_start_time = 0
        service._recording_samplerate = 16000
        service._audio_buffer = [np.array([0.1, 0.2, 0.3], dtype=np.float32)]

        mock_model = Mock()
        mock_model.is_loaded = True
        mock_model.model_name = "test-model"
        service._model = mock_model

        return service

    def test_stop_and_transcribe_stops_recording(self, service_with_model):
        """Test that stop_and_transcribe stops the recording."""
        service = service_with_model

        with patch.object(service, "stop_recording") as mock_stop:
            with patch.object(service, "transcribe") as mock_transcribe:
                mock_stop.return_value = Mock(
                    audio_data=np.array([0.1, 0.2, 0.3]), sample_rate=16000, duration_seconds=1.0
                )
                mock_transcribe.return_value = TranscriptionResult(
                    text="Transcribed text",
                    duration_ms=1000,
                    language="en",
                    model_used="test-model",
                )

                service.stop_and_transcribe()

                mock_stop.assert_called_once()

    def test_stop_and_transcribe_calls_transcribe(self, service_with_model):
        """Test that stop_and_transcribe calls transcribe."""
        service = service_with_model

        with patch.object(service, "stop_recording") as mock_stop:
            with patch.object(service, "transcribe") as mock_transcribe:
                mock_stop.return_value = Mock(
                    audio_data=np.array([0.1, 0.2, 0.3]), sample_rate=16000, duration_seconds=1.0
                )
                mock_transcribe.return_value = TranscriptionResult(
                    text="Test",
                    duration_ms=1000,
                )

                service.stop_and_transcribe()

                mock_transcribe.assert_called_once()

    def test_stop_and_transcribe_returns_result(self, service_with_model):
        """Test that stop_and_transcribe returns transcription result."""
        service = service_with_model

        with patch.object(service, "stop_recording") as mock_stop:
            with patch.object(service, "transcribe") as mock_transcribe:
                mock_stop.return_value = Mock(
                    audio_data=np.array([0.1, 0.2, 0.3]), sample_rate=16000, duration_seconds=1.0
                )
                mock_transcribe.return_value = TranscriptionResult(
                    text="Transcribed text",
                    duration_ms=1000,
                    language="en",
                    model_used="test-model",
                )

                result = service.stop_and_transcribe()

                assert isinstance(result, TranscriptionResult)
                assert result.text == "Transcribed text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
