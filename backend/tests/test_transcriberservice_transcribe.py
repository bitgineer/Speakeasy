"""
Test for TranscriberService.transcribe
Comprehensive test suite for transcribing audio data.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState, TranscriptionResult


class TestTranscriberServiceTranscribe:
    """Tests for TranscriberService.transcribe"""

    @pytest.fixture
    def service_with_model(self):
        """Create a service with a loaded model."""
        service = TranscriberService()
        mock_model = Mock()
        mock_model.is_loaded = True
        mock_model.model_name = "test-model"
        mock_model.transcribe.return_value = TranscriptionResult(
            text="Transcribed text",
            duration_ms=500,
            language="en",
            model_used="test-model",
        )
        service._model = mock_model
        service._state = TranscriberState.READY
        return service

    def test_transcribe_no_model_raises_error(self):
        """Test that transcribe raises error when no model loaded."""
        service = TranscriberService()
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with pytest.raises(RuntimeError, match="No model loaded"):
            service.transcribe(audio_data)

    def test_transcribe_sets_transcribing_state(self, service_with_model):
        """Test that transcribe sets state to TRANSCRIBING."""
        service = service_with_model
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with patch.object(service, "_set_state") as mock_set_state:
            service.transcribe(audio_data)

            assert any(
                call[0][0] == TranscriberState.TRANSCRIBING
                for call in mock_set_state.call_args_list
            )

    def test_transcribe_returns_result(self, service_with_model):
        """Test that transcribe returns TranscriptionResult."""
        service = service_with_model
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        result = service.transcribe(audio_data)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Transcribed text"

    def test_transcribe_resets_to_ready_state(self, service_with_model):
        """Test that transcribe resets state to READY after completion."""
        service = service_with_model
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        service.transcribe(audio_data)

        assert service._state == TranscriberState.READY

    def test_transcribe_with_language(self, service_with_model):
        """Test transcribe with language parameter."""
        service = service_with_model
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        result = service.transcribe(audio_data, language="es")

        # Verify model.transcribe was called with language
        service._model.transcribe.assert_called_once()
        call_kwargs = service._model.transcribe.call_args.kwargs
        assert call_kwargs.get("language") == "es"

    def test_transcribe_with_instruction(self, service_with_model):
        """Test transcribe with instruction parameter."""
        service = service_with_model
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        service.transcribe(audio_data, instruction="Correct grammar")

        # Verify model.transcribe was called with instruction
        call_kwargs = service._model.transcribe.call_args.kwargs
        assert call_kwargs.get("instruction") == "Correct grammar"

    def test_transcribe_handles_error(self, service_with_model):
        """Test that transcribe handles errors and sets ERROR state."""
        service = service_with_model
        service._model.transcribe.side_effect = Exception("Transcription failed")
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with pytest.raises(Exception, match="Transcription failed"):
            service.transcribe(audio_data)

        assert service._state == TranscriberState.ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
