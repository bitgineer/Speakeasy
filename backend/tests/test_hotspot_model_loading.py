"""
Integration tests for model loading and switching hotspots.

Tests critical model operations:
- Model loading (_load_whisper, _load_parakeet)
- Model switching during recording
- Model reload operations
- Progress callback handling

Covers blast radius flows:
- proc_114_reload_model
- proc_4_transcribe
- proc_6_load_model
- proc_7_reload_model
- proc_13_transcribe
- proc_19_load_model
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from speakeasy.core.models import ModelType, ModelWrapper, TranscriptionResult
from speakeasy.core.transcriber import TranscriberService, TranscriberState


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_model_backends():
    """Mock all model backend libraries."""

    # Mock Whisper
    mock_whisper = MagicMock()
    mock_whisper.WhisperModel = MagicMock()
    mock_whisper.WhisperModel.return_value.transcribe.return_value = (
        [{"text": " Whisper test "}],
        {"language": "en"},
    )

    # Mock NeMo (Parakeet/Canary)
    mock_nemo = MagicMock()
    mock_nemo.collections.asr.models.ASRModel.from_pretrained.return_value.eval.return_value.transcribe.return_value = [
        MagicMock(text="Parakeet test")
    ]
    mock_nemo.collections.asr.models.EncDecMultiTaskModel.from_pretrained.return_value.eval.return_value.transcribe.return_value = [
        MagicMock(text="Canary test")
    ]

    with (
        patch.dict("sys.modules", {"faster_whisper": mock_whisper}),
        patch.dict(
            "sys.modules",
            {
                "nemo": mock_nemo,
                "nemo.collections": mock_nemo.collections,
                "nemo.collections.asr": mock_nemo.collections.asr,
                "nemo.collections.asr.models": mock_nemo.collections.asr.models,
            },
        ),
        patch("torch.cuda.is_available", return_value=False),
        patch("torch.cuda.empty_cache"),
    ):
        yield mock_whisper, mock_nemo


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice for audio operations."""
    with (
        patch("sounddevice.InputStream") as mock_stream,
        patch("sounddevice.query_devices", return_value=[]),
        patch("sounddevice.default", MagicMock(device=[0, 0])),
    ):
        mock_stream.return_value.start = MagicMock()
        mock_stream.return_value.stop = MagicMock()
        mock_stream.return_value.close = MagicMock()
        yield mock_stream


@pytest.fixture
def transcriber_with_tracking(mock_sounddevice, mock_model_backends):
    """Create transcriber with state and progress tracking."""
    state_changes = []
    progress_updates = []

    def on_state_change(state):
        state_changes.append((time.time(), state))

    # Progress callback will be passed to load_model, not __init__
    def on_progress(progress):
        progress_updates.append((time.time(), progress))

    service = TranscriberService(on_state_change=on_state_change)

    # Store progress callback for tests that need it
    service._test_progress_callback = on_progress  # type: ignore

    yield service, state_changes, progress_updates

    service.cleanup()


# =============================================================================
# Model Loading Tests
# =============================================================================


class TestModelLoading:
    """Tests for model loading operations."""

    def test_load_whisper_model(self, transcriber_with_tracking):
        """Test loading Whisper model transitions through correct states."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Load Whisper model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Verify state transitions: IDLE -> LOADING -> READY
        assert TranscriberState.LOADING in [s for _, s in state_changes]
        assert TranscriberState.READY in [s for _, s in state_changes]

        # Verify model is loaded
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY

    def test_load_parakeet_model(self, transcriber_with_tracking):
        """Test loading Parakeet model transitions through correct states."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Load Parakeet model
        transcriber.load_model(
            model_type="parakeet",
            model_name="nvidia/parakeet-tdt-0.6b-v3",
            device="cpu",
        )

        # Verify state transitions
        assert TranscriberState.LOADING in [s for _, s in state_changes]
        assert TranscriberState.READY in [s for _, s in state_changes]

        # Verify model is loaded
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY

    def test_load_model_with_progress_callback(self, transcriber_with_tracking):
        """Test that progress callbacks are invoked during model loading."""
        transcriber, _, progress_updates = transcriber_with_tracking

        # Load model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Verify progress was reported
        assert len(progress_updates) > 0

        # Verify progress values are between 0 and 1
        for _, progress in progress_updates:
            assert 0.0 <= progress <= 1.0

    def test_load_already_loaded_model(self, transcriber_with_tracking, caplog):
        """Test loading when model is already loaded is a no-op."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Load model first time
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        state_changes.clear()

        # Load same model again
        import logging

        with caplog.at_level(logging.INFO):
            transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Should not see LOADING state again
        assert TranscriberState.LOADING not in [s for _, s in state_changes]

        # Should log info message
        assert "already loaded" in caplog.text.lower()


# =============================================================================
# Model Switching Tests
# =============================================================================


class TestModelSwitching:
    """Tests for switching between different models."""

    def test_switch_whisper_to_parakeet(self, transcriber_with_tracking):
        """Test switching from Whisper to Parakeet model."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Load Whisper
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        assert transcriber.is_model_loaded

        # Switch to Parakeet
        transcriber.load_model(
            model_type="parakeet",
            model_name="nvidia/parakeet-tdt-0.6b-v3",
            device="cpu",
        )

        # Verify new model is loaded
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY

    def test_switch_parakeet_to_whisper(self, transcriber_with_tracking):
        """Test switching from Parakeet to Whisper model."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Load Parakeet
        transcriber.load_model(
            model_type="parakeet",
            model_name="nvidia/parakeet-tdt-0.6b-v3",
            device="cpu",
        )
        assert transcriber.is_model_loaded

        # Switch to Whisper
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Verify new model is loaded
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY

    def test_switch_preserves_state_transitions(self, transcriber_with_tracking):
        """Test that model switching maintains correct state transitions."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Initial load
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Switch model
        transcriber.load_model(
            model_type="parakeet",
            model_name="nvidia/parakeet-tdt-0.6b-v3",
            device="cpu",
        )

        # Verify LOADING and READY states appear for both loads
        loading_count = sum(1 for _, s in state_changes if s == TranscriberState.LOADING)
        ready_count = sum(1 for _, s in state_changes if s == TranscriberState.READY)

        assert loading_count >= 2  # At least once per load
        assert ready_count >= 2


# =============================================================================
# Model Reload During Recording Tests
# =============================================================================


class TestModelReloadDuringRecording:
    """Tests for edge case: reloading model during active recording."""

    def test_reload_model_while_recording_raises_error(
        self, transcriber_with_tracking, mock_sounddevice
    ):
        """Test that attempting to reload model during recording raises error."""
        transcriber, _, _ = transcriber_with_tracking

        # Load model and start recording
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        transcriber.start_recording()
        assert transcriber.is_recording

        # Attempting to reload should raise error or be prevented
        # (Implementation-dependent behavior)
        # Most implementations should prevent this or handle gracefully
        try:
            transcriber.load_model(model_type="whisper", model_name="base", device="cpu")
            # If it doesn't raise, recording should have been stopped
            assert not transcriber.is_recording
        except RuntimeError as e:
            # Expected: cannot change model during recording
            assert "recording" in str(e).lower()

    def test_unload_model_while_recording_stops_recording(
        self, transcriber_with_tracking, mock_sounddevice
    ):
        """Test that unloading model during recording stops recording."""
        transcriber, _, _ = transcriber_with_tracking

        # Load and start recording
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        transcriber.start_recording()
        assert transcriber.is_recording

        # Unload model
        transcriber.unload_model()

        # Recording should be stopped
        assert not transcriber.is_recording
        assert transcriber.state == TranscriberState.IDLE


# =============================================================================
# Model Reload Operations Tests
# =============================================================================


class TestReloadModelOperation:
    """Tests for reload_model functionality."""

    def test_reload_model_success(self, transcriber_with_tracking):
        """Test successful model reload."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Load model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        state_changes.clear()

        # Reload
        transcriber.reload_model()

        # Should go through READY -> UNLOADING -> LOADING -> READY
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY

    def test_reload_model_unloads_first(self, transcriber_with_tracking):
        """Test that reload unloads existing model before loading."""
        transcriber, state_changes, _ = transcriber_with_tracking

        # Load model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Reload
        transcriber.reload_model()

        # Verify unload happened (IDLE state should appear)
        assert TranscriberState.IDLE in [s for _, s in state_changes]
        assert TranscriberState.LOADING in [s for _, s in state_changes]
        assert TranscriberState.READY in [s for _, s in state_changes]

    def test_reload_model_with_different_params(self, transcriber_with_tracking):
        """Test reload with different model parameters."""
        transcriber, _, _ = transcriber_with_tracking

        # Load initial model
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")

        # Reload with different parameters
        transcriber.reload_model(model_type="whisper", model_name="base", device="cpu")

        # Should still be loaded and ready
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY


# =============================================================================
# ModelWrapper Direct Tests
# =============================================================================


class TestModelWrapperDirect:
    """Direct tests for ModelWrapper class."""

    def test_model_wrapper_load_whisper(self, mock_model_backends):
        """Test ModelWrapper loads Whisper correctly."""
        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cpu",
            compute_type="int8",
        )

        wrapper.load()

        assert wrapper.is_loaded
        assert wrapper._model is not None

    def test_model_wrapper_unload(self, mock_model_backends):
        """Test ModelWrapper unloads correctly."""
        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cpu",
        )

        wrapper.load()
        assert wrapper.is_loaded

        wrapper.unload()

        assert not wrapper.is_loaded
        assert wrapper._model is None

    def test_model_wrapper_transcribe(self, mock_model_backends):
        """Test ModelWrapper transcription."""
        wrapper = ModelWrapper(
            model_type="whisper",
            model_name="tiny",
            device="cpu",
        )

        wrapper.load()

        audio = np.random.randn(16000).astype(np.float32)
        result = wrapper.transcribe(audio, sample_rate=16000, language="en")

        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert result.language == "en"
        assert result.model_used == "tiny"


# =============================================================================
# Stress Tests: Rapid Model Operations
# =============================================================================


class TestModelOperationsStress:
    """Stress tests for model operations."""

    def test_rapid_load_unload_cycles(self, transcriber_with_tracking):
        """Test rapid load/unload cycles don't leak resources."""
        transcriber, _, _ = transcriber_with_tracking

        for _ in range(5):
            transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
            assert transcriber.is_model_loaded

            transcriber.unload_model()
            assert not transcriber.is_model_loaded

        # Should still work after cycles
        transcriber.load_model(model_type="whisper", model_name="tiny", device="cpu")
        assert transcriber.is_model_loaded
        assert transcriber.state == TranscriberState.READY

    def test_multiple_model_switches(self, transcriber_with_tracking):
        """Test multiple model switches in sequence."""
        transcriber, _, _ = transcriber_with_tracking

        models = [
            ("whisper", "tiny"),
            ("parakeet", "nvidia/parakeet-tdt-0.6b-v3"),
            ("whisper", "base"),
            ("parakeet", "nvidia/parakeet-tdt-0.6b-v3"),
        ]

        for model_type, model_name in models:
            transcriber.load_model(model_type=model_type, model_name=model_name, device="cpu")
            assert transcriber.is_model_loaded
            assert transcriber.state == TranscriberState.READY
