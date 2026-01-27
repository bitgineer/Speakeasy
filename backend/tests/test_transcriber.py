"""
Comprehensive tests for TranscriberService state machine.

Tests cover all state transitions, error cases, and resource management.
"""

import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from speakeasy.core.transcriber import TranscriberService, TranscriberState


# =============================================================================
# Mock Classes
# =============================================================================


class MockInputStream:
    """Mock sounddevice.InputStream for testing without hardware access."""

    def __init__(self, **kwargs):
        self.callback = kwargs.get("callback")
        self.samplerate = kwargs.get("samplerate", 16000)
        self.channels = kwargs.get("channels", 1)
        self.dtype = kwargs.get("dtype", np.float32)
        self.device = kwargs.get("device")
        self._running = False
        self._thread = None

    def start(self):
        """Start the mock stream."""
        self._running = True

    def stop(self):
        """Stop the mock stream."""
        self._running = False

    def close(self):
        """Close the mock stream."""
        self._running = False

    def simulate_audio(self, duration_seconds: float = 0.1):
        """Simulate audio data being captured."""
        if self.callback and self._running:
            # Generate fake audio data
            samples = int(self.samplerate * duration_seconds)
            audio_data = np.random.randn(samples, self.channels).astype(np.float32)
            self.callback(audio_data, samples, {}, None)


class MockModelWrapper:
    """Mock ModelWrapper for testing without loading real models."""

    def __init__(self, **kwargs):
        self.model_type = kwargs.get("model_type", "whisper")
        self.model_name = kwargs.get("model_name", "tiny")
        self.device = kwargs.get("device", "cpu")
        self.compute_type = kwargs.get("compute_type", "int8")
        self._loaded = False
        self._should_fail_load = False
        self._should_fail_transcribe = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self, progress_callback=None):
        if self._should_fail_load:
            raise RuntimeError("Mock model load failure")
        self._loaded = True

    def unload(self):
        self._loaded = False

    def transcribe(self, audio_data, sample_rate=16000, language=None):
        if self._should_fail_transcribe:
            raise RuntimeError("Mock transcription failure")
        # Return a mock TranscriptionResult
        mock_result = MagicMock()
        mock_result.text = "Test transcription"
        mock_result.duration_ms = 100
        mock_result.language = language
        mock_result.model_used = self.model_name
        return mock_result


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice module to avoid hardware access."""
    mock_devices = [
        {
            "name": "Default Microphone",
            "max_input_channels": 2,
            "max_output_channels": 0,
            "default_samplerate": 44100.0,
        },
        {
            "name": "USB Audio Device",
            "max_input_channels": 1,
            "max_output_channels": 0,
            "default_samplerate": 48000.0,
        },
        {
            "name": "Speakers",
            "max_input_channels": 0,
            "max_output_channels": 2,
            "default_samplerate": 44100.0,
        },
    ]
    mock_default = MagicMock()
    mock_default.device = [0, 2]  # [input_device, output_device]

    with (
        patch("sounddevice.query_devices", return_value=mock_devices),
        patch("sounddevice.InputStream", MockInputStream),
        patch("sounddevice.default", mock_default),
    ):
        yield


@pytest.fixture
def mock_model_wrapper():
    """Mock ModelWrapper to avoid loading real models."""
    with patch("speakeasy.core.transcriber.ModelWrapper", MockModelWrapper) as mock_class:
        yield mock_class


@pytest.fixture
def transcriber(mock_sounddevice, mock_model_wrapper):
    """Create a TranscriberService with mocked dependencies."""
    service = TranscriberService()
    yield service
    # Cleanup
    service.cleanup()


@pytest.fixture
def transcriber_with_callback(mock_sounddevice, mock_model_wrapper):
    """Create a TranscriberService with a state change callback."""
    state_changes = []

    def on_state_change(state):
        state_changes.append(state)

    service = TranscriberService(on_state_change=on_state_change)
    yield service, state_changes
    service.cleanup()


@pytest.fixture
def loaded_transcriber(transcriber):
    """Create a TranscriberService with a model already loaded."""
    transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
    return transcriber


# =============================================================================
# Test Cases
# =============================================================================


class TestInitialState:
    """Tests for initial state."""

    def test_initial_state_idle(self, transcriber):
        """Test that transcriber starts in IDLE state."""
        assert transcriber.state == TranscriberState.IDLE
        assert not transcriber.is_model_loaded
        assert not transcriber.is_recording


class TestLoadModel:
    """Tests for model loading transitions."""

    def test_load_model_transitions(self, transcriber_with_callback):
        """Test IDLE -> LOADING -> READY transitions on successful load."""
        transcriber, state_changes = transcriber_with_callback

        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        assert transcriber.state == TranscriberState.READY
        assert transcriber.is_model_loaded
        assert TranscriberState.LOADING in state_changes
        assert TranscriberState.READY in state_changes

    def test_load_model_error_transitions(self, transcriber_with_callback):
        """Test IDLE -> LOADING -> ERROR transitions on load failure."""
        transcriber, state_changes = transcriber_with_callback

        # Make the mock model fail to load
        with patch("speakeasy.core.transcriber.ModelWrapper") as mock_class:
            mock_instance = MockModelWrapper()
            mock_instance._should_fail_load = True
            mock_class.return_value = mock_instance

            with pytest.raises(RuntimeError, match="Mock model load failure"):
                transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        assert transcriber.state == TranscriberState.ERROR
        assert TranscriberState.LOADING in state_changes
        assert TranscriberState.ERROR in state_changes


class TestUnloadModel:
    """Tests for model unloading."""

    def test_unload_model_to_idle(self, loaded_transcriber):
        """Test READY -> IDLE transition on unload."""
        assert loaded_transcriber.state == TranscriberState.READY

        loaded_transcriber.unload_model()

        assert loaded_transcriber.state == TranscriberState.IDLE
        assert not loaded_transcriber.is_model_loaded


class TestStartRecording:
    """Tests for starting recording."""

    def test_start_recording_transitions(self, loaded_transcriber):
        """Test READY -> RECORDING transition."""
        loaded_transcriber.start_recording()

        assert loaded_transcriber.state == TranscriberState.RECORDING
        assert loaded_transcriber.is_recording

    def test_start_recording_requires_model(self, transcriber):
        """Test that start_recording raises RuntimeError without model."""
        with pytest.raises(RuntimeError, match="No model loaded"):
            transcriber.start_recording()

    def test_start_recording_already_recording(self, loaded_transcriber, caplog):
        """Test that starting recording while already recording logs warning."""
        loaded_transcriber.start_recording()
        assert loaded_transcriber.is_recording

        # Try to start again - should log warning but not error
        loaded_transcriber.start_recording()

        assert loaded_transcriber.is_recording
        assert "Already recording" in caplog.text


class TestStopRecording:
    """Tests for stopping recording."""

    def test_stop_recording_transitions(self, loaded_transcriber):
        """Test RECORDING -> READY transition with audio data."""
        loaded_transcriber.start_recording()

        # Simulate some audio being captured
        stream = loaded_transcriber._stream
        if isinstance(stream, MockInputStream):
            stream.simulate_audio(duration_seconds=0.5)

        result = loaded_transcriber.stop_recording()

        assert loaded_transcriber.state == TranscriberState.READY
        assert not loaded_transcriber.is_recording
        assert result.audio_data is not None
        assert result.sample_rate == 16000

    def test_stop_recording_not_recording(self, loaded_transcriber):
        """Test that stop_recording raises RuntimeError when not recording."""
        with pytest.raises(RuntimeError, match="Not recording"):
            loaded_transcriber.stop_recording()

    def test_stop_recording_empty_buffer(self, loaded_transcriber):
        """Test that stop_recording raises RuntimeError with empty buffer."""
        loaded_transcriber.start_recording()
        # Don't simulate any audio - buffer stays empty

        with pytest.raises(RuntimeError, match="No audio"):
            loaded_transcriber.stop_recording()


class TestTranscribe:
    """Tests for transcription."""

    def test_transcribe_transitions(self, transcriber_with_callback):
        """Test READY -> TRANSCRIBING -> READY transitions."""
        transcriber, state_changes = transcriber_with_callback

        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        state_changes.clear()

        audio_data = np.random.randn(16000).astype(np.float32)
        result = transcriber.transcribe(audio_data)

        assert transcriber.state == TranscriberState.READY
        assert TranscriberState.TRANSCRIBING in state_changes
        assert result.text == "Test transcription"

    def test_transcribe_requires_model(self, transcriber):
        """Test that transcribe raises RuntimeError without model."""
        audio_data = np.random.randn(16000).astype(np.float32)

        with pytest.raises(RuntimeError, match="No model loaded"):
            transcriber.transcribe(audio_data)


class TestStopAndTranscribe:
    """Tests for combined stop and transcribe operation."""

    def test_stop_and_transcribe(self, loaded_transcriber):
        """Test combined stop_recording and transcribe operation."""
        loaded_transcriber.start_recording()

        # Simulate audio
        stream = loaded_transcriber._stream
        if isinstance(stream, MockInputStream):
            stream.simulate_audio(duration_seconds=0.5)

        result = loaded_transcriber.stop_and_transcribe()

        assert loaded_transcriber.state == TranscriberState.READY
        assert not loaded_transcriber.is_recording
        assert result.text == "Test transcription"


class TestCancelRecording:
    """Tests for canceling recording."""

    def test_cancel_recording(self, loaded_transcriber):
        """Test RECORDING -> READY transition on cancel."""
        loaded_transcriber.start_recording()
        assert loaded_transcriber.is_recording

        loaded_transcriber.cancel_recording()

        assert loaded_transcriber.state == TranscriberState.READY
        assert not loaded_transcriber.is_recording

    def test_cancel_not_recording(self, loaded_transcriber):
        """Test that cancel_recording is a no-op when not recording."""
        assert not loaded_transcriber.is_recording

        # Should not raise any error
        loaded_transcriber.cancel_recording()

        assert loaded_transcriber.state == TranscriberState.READY


class TestCleanup:
    """Tests for resource cleanup."""

    def test_cleanup(self, loaded_transcriber):
        """Test that cleanup releases all resources."""
        loaded_transcriber.start_recording()

        # Simulate audio
        stream = loaded_transcriber._stream
        if isinstance(stream, MockInputStream):
            stream.simulate_audio(duration_seconds=0.1)

        loaded_transcriber.cleanup()

        assert loaded_transcriber.state == TranscriberState.IDLE
        assert not loaded_transcriber.is_model_loaded
        assert not loaded_transcriber.is_recording
        assert loaded_transcriber._stream is None


class TestSetDevice:
    """Tests for audio device selection."""

    def test_set_device_valid(self, transcriber):
        """Test setting a valid audio device."""
        transcriber.set_device("Default Microphone")

        assert transcriber._device_name == "Default Microphone"
        assert transcriber._device_id == 0

    def test_set_device_partial_match(self, transcriber):
        """Test setting device with partial name match."""
        transcriber.set_device("USB")

        assert transcriber._device_name == "USB Audio Device"
        assert transcriber._device_id == 1

    def test_set_device_invalid(self, transcriber):
        """Test that setting invalid device raises ValueError."""
        with pytest.raises(ValueError, match="Audio device not found"):
            transcriber.set_device("Nonexistent Device")

    def test_set_device_none(self, transcriber):
        """Test setting device to None resets to default."""
        transcriber.set_device("Default Microphone")
        assert transcriber._device_id is not None

        transcriber.set_device(None)

        assert transcriber._device_name is None
        assert transcriber._device_id is None


class TestStateChangeCallback:
    """Tests for state change callback."""

    def test_state_change_callback(self, transcriber_with_callback):
        """Test that callback is invoked on all state transitions."""
        transcriber, state_changes = transcriber_with_callback

        # Load model: IDLE -> LOADING -> READY
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        assert TranscriberState.LOADING in state_changes
        assert TranscriberState.READY in state_changes

        # Start recording: READY -> RECORDING
        transcriber.start_recording()
        assert TranscriberState.RECORDING in state_changes

        # Cancel: RECORDING -> READY
        transcriber.cancel_recording()
        # READY should appear again
        assert state_changes.count(TranscriberState.READY) >= 2

    def test_callback_exception_handled(self, mock_sounddevice, mock_model_wrapper):
        """Test that callback exceptions are caught and logged."""

        def bad_callback(state):
            raise ValueError("Callback error")

        transcriber = TranscriberService(on_state_change=bad_callback)

        # Should not raise despite callback error
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        assert transcriber.state == TranscriberState.READY
        transcriber.cleanup()


class TestProperties:
    """Tests for property accessors."""

    def test_is_model_loaded_property(self, transcriber, loaded_transcriber):
        """Test is_model_loaded property reflects actual state."""
        assert not transcriber.is_model_loaded
        assert loaded_transcriber.is_model_loaded

        loaded_transcriber.unload_model()
        assert not loaded_transcriber.is_model_loaded

    def test_is_recording_property(self, loaded_transcriber):
        """Test is_recording property reflects state."""
        assert not loaded_transcriber.is_recording

        loaded_transcriber.start_recording()
        assert loaded_transcriber.is_recording

        loaded_transcriber.cancel_recording()
        assert not loaded_transcriber.is_recording
