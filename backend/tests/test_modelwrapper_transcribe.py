"""
Test for ModelWrapper.transcribe
Comprehensive test suite for transcribing audio.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.models import ModelWrapper, ModelType, TranscriptionResult


class TestModelWrapperTranscribe:
    """Tests for ModelWrapper.transcribe"""

    def test_transcribe_raises_when_not_loaded(self):
        """Test that transcribe raises error when model not loaded."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with pytest.raises(RuntimeError, match="Model not loaded"):
            wrapper.transcribe(audio_data)

    def test_transcribe_whisper(self):
        """Test transcribe with whisper model."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        wrapper._loaded = True
        wrapper._model = Mock()
        wrapper._model.transcribe.return_value = [Mock(text="Hello world")]

        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with patch.object(wrapper, "_transcribe_whisper", return_value="Hello world"):
            result = wrapper.transcribe(audio_data)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hello world"

    def test_transcribe_returns_result_with_metadata(self):
        """Test that transcribe returns result with proper metadata."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        wrapper._loaded = True

        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with patch.object(wrapper, "_transcribe_whisper", return_value="Transcribed text"):
            result = wrapper.transcribe(audio_data, language="en")

        assert result.text == "Transcribed text"
        assert result.language == "en"
        assert result.model_used == "small"
        assert result.duration_ms >= 0

    def test_transcribe_with_language(self):
        """Test transcribe with language parameter."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        wrapper._loaded = True

        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with patch.object(wrapper, "_transcribe_whisper", return_value="Hola mundo"):
            result = wrapper.transcribe(audio_data, language="es")

        assert result.language == "es"

    def test_transcribe_with_instruction(self):
        """Test transcribe with instruction parameter."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        wrapper._loaded = True

        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with patch.object(wrapper, "_transcribe_whisper", return_value="Corrected text"):
            result = wrapper.transcribe(audio_data, instruction="Correct grammar")

        assert result.text == "Corrected text"

    def test_transcribe_error_handling(self):
        """Test that transcribe handles errors properly."""
        wrapper = ModelWrapper(model_type="whisper", model_name="small")
        wrapper._loaded = True

        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with patch.object(
            wrapper, "_transcribe_whisper", side_effect=Exception("Transcription error")
        ):
            with pytest.raises(Exception, match="Transcription error"):
                wrapper.transcribe(audio_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
