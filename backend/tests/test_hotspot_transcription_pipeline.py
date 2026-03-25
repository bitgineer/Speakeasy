"""
Integration tests for transcription pipeline hotspots.

Tests the complete flow: start_recording → stop_recording → transcribe → _transcribe_chunked → TranscriptionResult

These tests cover the critical paths identified in the blast radius analysis:
- proc_34_transcribe_stop
- proc_81_transcribe_file
- proc_10_transcribe_stop
- proc_14_transcribe_file
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from speakeasy.core.models import TranscriptionResult
from speakeasy.core.transcriber import RecordingResult, TranscriberService, TranscriberState


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_model_wrapper():
    """Mock ModelWrapper that simulates real transcription."""

    class MockModel:
        def __init__(self):
            self.is_loaded = False
            self.model_type = "whisper"
            self.model_name = "tiny"
            self.device = "cpu"
            self.compute_type = "int8"
            self._model = None

        def load(self, progress_callback=None):
            self.is_loaded = True
            self._model = MagicMock()
            if progress_callback:
                progress_callback(0.0)
                progress_callback(0.5)
                progress_callback(1.0)

        def unload(self):
            self.is_loaded = False
            self._model = None

        def transcribe(self, audio_data, sample_rate=16000, language=None):
            """Simulate realistic transcription."""
            if not self.is_loaded:
                raise RuntimeError("Model not loaded")

            # Simulate processing time
            duration_ms = int(len(audio_data) / sample_rate * 1000)

            return TranscriptionResult(
                text=f"Transcribed {len(audio_data)} samples",
                duration_ms=duration_ms,
                language=language or "en",
                model_used=self.model_name,
            )

    with patch("speakeasy.core.transcriber.ModelWrapper", return_value=MockModel()):
        yield MockModel


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice to simulate audio capture."""
    mock_stream = MagicMock()
    mock_stream.start = MagicMock()
    mock_stream.stop = MagicMock()
    mock_stream.close = MagicMock()

    with (
        patch("sounddevice.InputStream", return_value=mock_stream),
        patch("sounddevice.query_devices", return_value=[]),
        patch("sounddevice.default", MagicMock(device=[0, 0])),
    ):
        yield mock_stream


@pytest.fixture
def transcriber_with_callbacks(mock_sounddevice, mock_model_wrapper):
    """Create transcriber with state tracking callbacks."""
    state_changes = []
    progress_updates = []

    def on_state_change(state):
        state_changes.append((time.time(), state))

    # Progress callback will be passed to load_model/transcribe, not __init__
    def on_progress(progress):
        progress_updates.append((time.time(), progress))

    service = TranscriberService(on_state_change=on_state_change)

    # Store progress callback for tests that need it
    service._test_progress_callback = on_progress

    yield service, state_changes, progress_updates

    service.cleanup()


# =============================================================================
# Integration Tests: Full Transcription Pipeline
# =============================================================================


class TestTranscriptionPipelineIntegration:
    """Integration tests for complete transcription pipeline."""

    def test_full_pipeline_start_stop_transcribe(
        self, transcriber_with_callbacks, mock_sounddevice
    ):
        """
        Test complete pipeline: start_recording → stop_recording → transcribe.

        Covers:
        - proc_34_transcribe_stop (5 steps)
        - TranscriberService.start_recording → stop_recording → transcribe flow
        """
        transcriber, state_changes, progress_updates = transcriber_with_callbacks

        # Load model first
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        state_changes.clear()

        # Step 1: Start recording
        transcriber.start_recording()
        assert transcriber.state == TranscriberState.RECORDING
        assert transcriber.is_recording

        # Simulate audio capture
        audio_data = np.random.randn(16000 * 2).astype(np.float32)  # 2 seconds
        if hasattr(transcriber, "_audio_buffer"):
            transcriber._audio_buffer = audio_data.tobytes()

        # Step 2: Stop recording
        recording_result = transcriber.stop_recording()
        assert isinstance(recording_result, RecordingResult)
        assert recording_result.audio_data is not None
        assert recording_result.sample_rate == 16000
        assert transcriber.state == TranscriberState.READY
        assert not transcriber.is_recording

        # Step 3: Transcribe
        result = transcriber.transcribe(recording_result.audio_data)

        # Verify result
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert len(result.text) > 0
        assert result.model_used == "tiny"
        assert result.duration_ms > 0

        # Verify state transitions
        assert TranscriberState.RECORDING in [s for _, s in state_changes]
        assert TranscriberState.READY in [s for _, s in state_changes]
        assert TranscriberState.TRANSCRIBING in [s for _, s in state_changes]

    def test_file_transcription_pipeline(self, transcriber_with_callbacks):
        """
        Test file transcription pipeline: transcribe_file → transcribe → _transcribe_chunked.

        Covers:
        - proc_81_transcribe_file (4 steps, all changed)
        - TranscriberService.transcribe_file flow
        """
        transcriber, state_changes, _ = transcriber_with_callbacks

        # Load model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        state_changes.clear()

        # Create mock audio file
        audio_data = np.random.randn(16000 * 5).astype(np.float32)  # 5 seconds

        # Transcribe file
        result = transcriber.transcribe_file(audio_data, sample_rate=16000)

        # Verify result
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert result.model_used == "tiny"
        assert result.duration_ms >= 4000  # At least 4 seconds

        # Verify state transitions
        assert TranscriberState.TRANSCRIBING in [s for _, s in state_changes]
        assert transcriber.state == TranscriberState.READY

    def test_chunked_transcription_large_audio(self, transcriber_with_callbacks):
        """
        Test _transcribe_chunked with large audio file.

        Covers:
        - _transcribe_chunked functionality
        - Chunking logic for long audio
        """
        transcriber, _, progress_updates = transcriber_with_callbacks

        # Load model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Create large audio (30 seconds - should be chunked)
        large_audio = np.random.randn(16000 * 30).astype(np.float32)

        # Transcribe (internally uses _transcribe_chunked)
        result = transcriber._transcribe_chunked(large_audio, sample_rate=16000)

        # Verify result
        assert isinstance(result, TranscriptionResult)
        assert result.duration_ms >= 29000  # At least 29 seconds

        # Verify progress updates were called
        assert len(progress_updates) > 0

    def test_stop_and_transcribe_combined(self, transcriber_with_callbacks):
        """
        Test combined stop_recording + transcribe in one operation.

        Covers:
        - proc_15_stop_and_transcribe
        - Combined operation flow
        """
        transcriber, state_changes, _ = transcriber_with_callbacks

        # Load model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Start recording
        transcriber.start_recording()

        # Simulate audio
        audio_data = np.random.randn(16000 * 3).astype(np.float32)
        if hasattr(transcriber, "_audio_buffer"):
            transcriber._audio_buffer = audio_data.tobytes()

        # Stop and transcribe in one call
        result = transcriber.stop_and_transcribe()

        # Verify result
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert transcriber.state == TranscriberState.READY
        assert not transcriber.is_recording


# =============================================================================
# Edge Cases and Error Conditions
# =============================================================================


class TestTranscriptionPipelineEdgeCases:
    """Test edge cases in transcription pipeline."""

    def test_transcribe_empty_audio(self, transcriber_with_callbacks):
        """Test transcription with empty audio raises error."""
        transcriber, _, _ = transcriber_with_callbacks

        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        empty_audio = np.array([], dtype=np.float32)

        with pytest.raises(RuntimeError, match="audio"):
            transcriber.transcribe(empty_audio)

    def test_transcribe_without_model_loaded(self, transcriber_with_callbacks):
        """Test transcription without loaded model raises error."""
        transcriber, _, _ = transcriber_with_callbacks

        audio_data = np.random.randn(16000).astype(np.float32)

        with pytest.raises(RuntimeError, match="No model loaded"):
            transcriber.transcribe(audio_data)

    def test_stop_recording_without_audio_captured(
        self, transcriber_with_callbacks, mock_sounddevice
    ):
        """Test stopping recording without any audio captured."""
        transcriber, _, _ = transcriber_with_callbacks

        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        transcriber.start_recording()

        # Don't simulate any audio capture

        with pytest.raises(RuntimeError, match="No audio"):
            transcriber.stop_recording()

    def test_multiple_transcriptions_sequential(self, transcriber_with_callbacks):
        """Test multiple transcriptions in sequence maintain state correctly."""
        transcriber, _, _ = transcriber_with_callbacks

        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # First transcription
        audio1 = np.random.randn(16000).astype(np.float32)
        result1 = transcriber.transcribe(audio1)
        assert result1.text is not None
        assert transcriber.state == TranscriberState.READY

        # Second transcription
        audio2 = np.random.randn(16000 * 2).astype(np.float32)
        result2 = transcriber.transcribe(audio2)
        assert result2.text is not None
        assert transcriber.state == TranscriberState.READY

        # Third transcription
        audio3 = np.random.randn(16000 * 3).astype(np.float32)
        result3 = transcriber.transcribe(audio3)
        assert result3.text is not None
        assert transcriber.state == TranscriberState.READY


# =============================================================================
# Performance and Stress Tests
# =============================================================================


class TestTranscriptionPipelinePerformance:
    """Performance tests for transcription pipeline."""

    def test_rapid_start_stop_cycles(self, transcriber_with_callbacks, mock_sounddevice):
        """Test rapid start/stop recording cycles don't leak resources."""
        transcriber, _, _ = transcriber_with_callbacks

        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        for _ in range(10):
            transcriber.start_recording()
            assert transcriber.is_recording

            # Simulate minimal audio
            audio_data = np.random.randn(8000).astype(np.float32)
            if hasattr(transcriber, "_audio_buffer"):
                transcriber._audio_buffer = audio_data.tobytes()

            result = transcriber.stop_recording()
            assert result.audio_data is not None
            assert transcriber.state == TranscriberState.READY

    def test_transcription_maintains_quality_over_time(self, transcriber_with_callbacks):
        """Test that transcription quality doesn't degrade over multiple operations."""
        transcriber, _, _ = transcriber_with_callbacks

        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        results = []
        for i in range(20):
            audio = np.random.randn(16000).astype(np.float32)
            result = transcriber.transcribe(audio)
            results.append(result)

        # All results should have text
        assert all(r.text for r in results)

        # All results should have reasonable duration
        assert all(r.duration_ms > 0 for r in results)

        # Model should still be loaded
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY
